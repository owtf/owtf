"""URL filters accept booleans as well as the HTTP query-string forms."""

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
from owtf.models.transaction import Transaction  # noqa: F401
from owtf.models.url import Url
from owtf.models.work import Work  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add_all(
            [Target(id=1, target_url="https://one.example"), Target(id=2, target_url="https://two.example")]
        )
        session.add_all(
            [
                Url(target_id=1, url="https://one.example/a", visited=False, scope=False),
                Url(target_id=1, url="https://one.example/b", visited=True, scope=True),
                Url(target_id=2, url="https://two.example/a", visited=False, scope=False),
            ]
        )
        session.commit()
        yield session
    engine.dispose()


@pytest.mark.parametrize("field", ["visited", "scope"])
@pytest.mark.parametrize("value", [False, 0, "false", "0", ["false"], True, "true", ["true"]])
def test_boolean_filter_selects_only_matching_rows(session, field, value):
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.url import url_gen_query

    expected = "https://one.example/a" if value in (False, 0, "false", "0", ["false"]) else "https://one.example/b"
    rows = url_gen_query(session, {field: value}, target_id=1).all()
    assert [row.url for row in rows] == [expected]


@pytest.mark.parametrize(
    "criteria",
    [
        {},
        {"visited": None},
        {"scope": None},
        {"visited": ""},
        {"scope": ""},
        {"visited": []},
        {"scope": []},
    ],
)
def test_absent_or_none_filter_does_not_exclude_rows(session, criteria):
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.url import url_gen_query

    assert url_gen_query(session, criteria, target_id=1).count() == 2
