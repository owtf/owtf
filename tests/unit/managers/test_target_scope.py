from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from owtf.db.model_base import Model
from owtf.models.command import Command  # noqa: F401
from owtf.models.grep_output import GrepOutput  # noqa: F401
from owtf.models.plugin import Plugin  # noqa: F401
from owtf.models.plugin_output import PluginOutput  # noqa: F401
from owtf.models.session import Session  # noqa: F401
from owtf.models.target import Target
from owtf.models.test_group import TestGroup as _TestGroup  # noqa: F401
from owtf.models.url import Url  # noqa: F401
from owtf.models.work import Work  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        group = Session(id=1, name="one")
        other = Session(id=2, name="two")
        group.targets = [
            Target(id=1, target_url="https://in.example", scope=True),
            Target(id=2, target_url="https://out.example", scope=False),
        ]
        other.targets = [Target(id=3, target_url="https://other.example", scope=False)]
        session.add_all([group, other])
        session.commit()
        yield session
    engine.dispose()


@pytest.mark.parametrize(
    "value, expected",
    [
        (False, [2]),
        (True, [1]),
        (0, [2]),
        (1, [1]),
        ("false", [2]),
        ("False", [2]),
        ("true", [1]),
        ("0", [2]),
        (["false"], [2]),
        (["true"], [1]),
    ],
)
def test_scope_filter_accepts_scalar_and_query_argument_forms(session, value, expected):
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.target import target_gen_query
    assert [row.id for row in target_gen_query(session, {"scope": value}, session_id=1).all()] == expected


@pytest.mark.parametrize("criteria", [{}, {"scope": None}, {"scope": ""}, {"scope": []}])
def test_empty_scope_filter_preserves_all_session_targets(session, criteria):
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.target import target_gen_query
    assert [row.id for row in target_gen_query(session, criteria, session_id=1).all()] == [2, 1]
