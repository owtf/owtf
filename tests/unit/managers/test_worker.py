"""
tests.unit.managers.test_worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for worker management and batch work fetching.
"""
from unittest import mock

from owtf.settings import WORKER_BATCH_SIZE, WORKER_HIGH_WATER, WORKER_LOW_WATER, WORKER_MAX_PROCESSES


def _get_work_batch():
    """Import get_work_batch without hitting a real DB connection.

    owtf.managers.worklist -> owtf.managers.poutput -> owtf.managers.target
    -> owtf.plugin.params opens a real DB session at import time.
    """
    with mock.patch("owtf.db.session.get_db_engine", return_value=mock.MagicMock()):
        from owtf.managers.worklist import get_work_batch
    return get_work_batch


def test_high_water_greater_than_low_water():
    """HIGH_WATER must be greater than LOW_WATER for proper scaling."""
    assert WORKER_HIGH_WATER > WORKER_LOW_WATER


def test_worker_batch_size_configured():
    """WORKER_BATCH_SIZE must be configured and positive."""
    assert WORKER_BATCH_SIZE > 0


def test_worker_max_processes_configured():
    """WORKER_MAX_PROCESSES must be configured and positive."""
    assert WORKER_MAX_PROCESSES > 0


def test_get_work_batch_respects_batch_size():
    """get_work_batch() must return at most batch_size items."""
    get_work_batch = _get_work_batch()
    from owtf.db.session import get_scoped_session

    session = get_scoped_session()
    try:
        batch_size = 3
        result = get_work_batch(session, [], ready_worker_count=batch_size, batch_size=batch_size)
        if result:
            assert len(result) <= batch_size, f"Expected at most {batch_size} items, got {len(result)}"
            # Each item is now (work_id, target, plugin)
            for item in result:
                assert len(item) == 3
    finally:
        session.close()


def test_get_work_batch_default_batch_size():
    """get_work_batch() should use WORKER_BATCH_SIZE when not specified."""
    get_work_batch = _get_work_batch()
    from owtf.db.session import get_scoped_session

    session = get_scoped_session()
    try:
        result = get_work_batch(session, [], ready_worker_count=WORKER_BATCH_SIZE)
        assert result is None or isinstance(result, list)
        if result:
            assert len(result) <= WORKER_BATCH_SIZE
    finally:
        session.close()


def test_work_batch_with_idle_workers_no_loss():
    """Batch work should not be lost when workers are idle."""
    get_work_batch = _get_work_batch()
    from owtf.db.session import get_scoped_session
    from owtf.models.work import Work

    session = get_scoped_session()
    try:
        for i in range(10):
            work = Work(target_id=1, plugin_key=f"plugin_{i}", active=True)
            session.add(work)
        session.commit()

        batch = get_work_batch(session, [], ready_worker_count=5, batch_size=5)
        assert len(batch) == 5
        for work_id, target, plugin in batch:
            assert work_id is not None

        remaining = session.query(Work).filter(Work.active.is_(True)).count()
        assert remaining == 5

        batch2 = get_work_batch(session, [], ready_worker_count=5, batch_size=5)
        assert len(batch2) == 5

        remaining = session.query(Work).filter(Work.active.is_(True)).count()
        assert remaining == 0
    finally:
        session.close()
