"""Unit tests for worker scaling settings and batch work fetching."""

from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.db.model_base import Model
from owtf.lib.exceptions import InvalidParameterType
from owtf.models.command import Command  # noqa: F401 - register Target relationship
from owtf.models.grep_output import GrepOutput  # noqa: F401 - register Transaction relationship
from owtf.models.plugin import Plugin
from owtf.models.plugin_output import PluginOutput  # noqa: F401 - register Plugin relationship
from owtf.models.session import Session  # noqa: F401 - register association-table foreign keys
from owtf.models.target import Target
from owtf.models.test_group import TestGroup as _TestGroup
from owtf.models.transaction import Transaction  # noqa: F401 - register Target relationship
from owtf.models.url import Url  # noqa: F401 - register Target relationship
from owtf.models.work import Work
from owtf.settings import WORKER_BATCH_SIZE, WORKER_HIGH_WATER, WORKER_LOW_WATER, WORKER_MAX_PROCESSES


def _get_work_batch():
    """Import worklist helpers without opening the configured PostgreSQL DB."""
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.worklist import get_work_batch

    return get_work_batch


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    try:
        yield db_session
    finally:
        db_session.close()


def _add_plugin(session, code, plugin_type, index):
    test_group = _TestGroup(
        code=code,
        group="web",
        descrip="test",
        url="https://example.test",
        priority=index,
    )
    plugin = Plugin(
        key=f"{plugin_type}@{code}",
        title=f"Plugin {index}",
        name=f"plugin_{index}",
        code=code,
        group="web",
        type=plugin_type,
        file=f"plugin_{index}.py",
    )
    target = Target(target_url=f"https://target-{index}.example")
    session.add_all([test_group, plugin, target])
    session.flush()
    work = Work(target_id=target.id, plugin_key=plugin.key, active=True)
    session.add(work)
    session.commit()
    return work


def test_high_water_greater_than_low_water():
    assert WORKER_HIGH_WATER > WORKER_LOW_WATER


def test_worker_batch_size_configured():
    assert WORKER_BATCH_SIZE > 0


def test_worker_max_processes_configured():
    assert WORKER_MAX_PROCESSES > 0


def test_get_work_batch_respects_ready_workers_and_priority(session):
    get_work_batch = _get_work_batch()
    low = _add_plugin(session, "OWTF-CM-003", "external", 1)
    high = _add_plugin(session, "OWTF-DV-005", "passive", 2)
    medium = _add_plugin(session, "OWTF-CM-004", "active", 3)

    batch = get_work_batch(session, [], ready_worker_count=2, batch_size=5, claim_owner="manager")

    assert [work_id for work_id, _target, _plugin in batch] == [high.id, medium.id]
    assert session.query(Work).filter(Work.claim_owner.is_(None)).one().id == low.id


def test_get_work_batch_uses_default_batch_size(session):
    get_work_batch = _get_work_batch()
    for index in range(WORKER_BATCH_SIZE + 1):
        _add_plugin(session, f"OWTF-TEST-{index:03d}", "passive", index)

    batch = get_work_batch(
        session,
        [],
        ready_worker_count=WORKER_BATCH_SIZE + 1,
        claim_owner="manager",
    )

    assert len(batch) == WORKER_BATCH_SIZE
    assert session.query(Work).filter(Work.claim_owner.is_(None)).count() == 1


@pytest.mark.parametrize("batch_size", [0, -1, "five"])
def test_get_work_batch_validates_batch_size(session, batch_size):
    get_work_batch = _get_work_batch()
    with pytest.raises(InvalidParameterType):
        get_work_batch(session, [], ready_worker_count=1, batch_size=batch_size, claim_owner="manager")


def test_expired_claims_are_recovered_after_restart_without_resuming_paused_work(session):
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.worklist import delete_work, get_work_batch, maintain_work_claims, patch_work

    interrupted = _add_plugin(session, "OWTF-TEST-001", "passive", 1)
    paused = _add_plugin(session, "OWTF-TEST-002", "passive", 2)
    interrupted_id, paused_id = interrupted.id, paused.id
    get_work_batch(session, [], ready_worker_count=2, claim_owner="old-manager")
    patch_work(session, paused_id, active=False)
    old_expiry = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
    interrupted.claim_expires_at = paused.claim_expires_at = old_expiry
    session.commit()

    # The surviving manager keeps its tracked claims alive, even if a cycle was delayed.
    maintain_work_claims(session, "old-manager", [interrupted_id, paused_id])
    assert interrupted.claim_expires_at > old_expiry
    interrupted.claim_expires_at = paused.claim_expires_at = old_expiry
    session.commit()

    # A new manager only knows the persisted queue and its own identity.
    with sessionmaker(bind=session.get_bind())() as restarted:
        maintain_work_claims(restarted, "new-manager", [])
        batch = get_work_batch(restarted, [], ready_worker_count=2, claim_owner="new-manager")
        assert [work_id for work_id, _target, _plugin in batch] == [interrupted_id]
        assert restarted.get(Work, paused_id).active is False
        assert restarted.get(Work, paused_id).claim_owner is None

        delete_work(restarted, interrupted_id, "old-manager")
        assert restarted.get(Work, interrupted_id).claim_owner == "new-manager"
