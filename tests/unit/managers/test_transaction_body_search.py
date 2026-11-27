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
from owtf.models.transaction import Transaction
from owtf.models.url import Url  # noqa: F401
from owtf.models.work import Work  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Model.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add_all(
            [Target(id=1, target_url="https://one.example"), Target(id=2, target_url="https://two.example")]
        )
        session.commit()
        yield session
    engine.dispose()


def query_transactions(session, criteria, for_stats=False):
    with mock.patch("owtf.db.session.get_scoped_session", return_value=mock.MagicMock()):
        from owtf.managers.transaction import transaction_gen_query
    return transaction_gen_query(session, criteria, target_id=1, for_stats=for_stats)


@pytest.mark.parametrize("needle", ["needle", ["needle"]])
def test_body_search_matches_text_and_excludes_binary_and_other_targets(session, needle):
    session.add_all(
        [
            Transaction(id=1, target_id=1, response_body="text with needle", binary_response=False),
            Transaction(id=2, target_id=1, response_body="needle in binary", binary_response=True),
            Transaction(id=3, target_id=1, response_body="unrelated text", binary_response=False),
            Transaction(id=4, target_id=2, response_body="needle on other target", binary_response=False),
        ]
    )
    session.commit()
    rows = query_transactions(session, {"search": True, "response_body": needle}).all()
    assert [row.id for row in rows] == [1]


def test_body_search_with_no_match_returns_no_rows(session):
    session.add(Transaction(target_id=1, response_body="plain text", binary_response=False))
    session.commit()
    assert query_transactions(session, {"search": True, "response_body": "missing"}).all() == []


def test_body_search_combines_with_url_search(session):
    session.add_all(
        [
            Transaction(
                id=1, target_id=1, url="https://one.example/wanted", response_body="needle", binary_response=False
            ),
            Transaction(
                id=2, target_id=1, url="https://one.example/other", response_body="needle", binary_response=False
            ),
        ]
    )
    session.commit()
    rows = query_transactions(session, {"search": True, "response_body": "needle", "url": "wanted"}).all()
    assert [row.id for row in rows] == [1]
