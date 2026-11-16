"""Removing a target from a session requires an existing membership."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.db.model_base import Model
from owtf.lib.exceptions import InvalidTargetReference
from owtf.managers.session import remove_target_from_session
from owtf.models.command import Command  # noqa: F401 - register Target relationship
from owtf.models.grep_output import GrepOutput  # noqa: F401 - register Transaction relationship
from owtf.models.plugin_output import PluginOutput  # noqa: F401 - register Plugin relationship
from owtf.models.session import Session
from owtf.models.target import Target
from owtf.models.transaction import Transaction  # noqa: F401 - register Target relationship
from owtf.models.url import Url  # noqa: F401 - register Target relationship
from owtf.models.work import Work  # noqa: F401 - register Target relationship


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    try:
        yield db_session
    finally:
        db_session.close()
        engine.dispose()


def test_remove_target_rejects_unlinked_session(session):
    first = Session(name="first")
    second = Session(name="second")
    target = Target(target_url="https://example.test")
    second.targets.append(target)
    session.add_all([first, second])
    session.commit()

    with pytest.raises(InvalidTargetReference):
        remove_target_from_session(session, target.id, session_id=first.id)

    session.expire_all()
    assert [item.id for item in target.sessions] == [second.id]
    assert session.query(Target).filter_by(id=target.id).count() == 1


def test_remove_target_keeps_membership_in_another_session(session):
    first = Session(name="first")
    second = Session(name="second")
    target = Target(target_url="https://example.test")
    first.targets.append(target)
    second.targets.append(target)
    session.add_all([first, second])
    session.commit()

    remove_target_from_session(session, target.id, session_id=first.id)

    session.expire_all()
    assert [item.id for item in target.sessions] == [second.id]
    assert session.query(Target).filter_by(id=target.id).count() == 1
