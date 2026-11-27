from datetime import datetime, timedelta
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


@pytest.fixture
def transactions(session):
    start = datetime(2026, 1, 1)
    # Insert in reverse chronological order so a missing ORDER BY is observable.
    for index in range(15):
        session.add(Transaction(id=index + 1, target_id=1, local_timestamp=start + timedelta(seconds=14 - index)))
    session.add(Transaction(id=99, target_id=2, local_timestamp=start))
    session.commit()
    return session


def test_default_page_is_limited_and_chronological(transactions):
    rows = query_transactions(transactions, {}).all()
    assert [row.id for row in rows] == list(range(15, 5, -1))


@pytest.mark.parametrize("criteria", [{"offset": ["3"], "limit": ["4"]}, {"offset": 3, "limit": 4}])
def test_explicit_page_is_chronological(transactions, criteria):
    rows = query_transactions(transactions, criteria).all()
    assert [row.id for row in rows] == [12, 11, 10, 9]


def test_statistics_query_is_not_paginated(transactions):
    assert query_transactions(transactions, {"limit": ["2"]}, for_stats=True).count() == 15


def test_offset_without_limit_still_has_a_default_page_size(transactions):
    assert len(query_transactions(transactions, {"offset": ["2"]}).all()) == 10
