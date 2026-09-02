"""Tests for the startup schema upgrader."""

import os

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

# Importing these models registers them on the shared metadata so
# create_all(tables=[...]) can resolve their foreign keys without
# pulling in unrelated tables.
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.db import upgrade as upgrade_module
from owtf.db.upgrade import run_startup_upgrades
from owtf.models.user import User
from owtf.models.user_plugin import UserPlugin

POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")


@pytest.fixture(autouse=True)
def _reset_upgrade_guard():
    # The upgrader runs at most once per process. Reset the guard so
    # each test starts from a clean state.
    upgrade_module._UPGRADES_APPLIED = False
    yield
    upgrade_module._UPGRADES_APPLIED = False


def _column_names(engine, table):
    return {c["name"] for c in inspect(engine).get_columns(table)}


def test_fresh_install_is_a_no_op():
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])
    before = _column_names(engine, "user_plugins")

    run_startup_upgrades(engine)

    after = _column_names(engine, "user_plugins")
    assert before == after
    # Sanity check that the fresh install already carries the review
    # trail columns.
    assert "rejection_reason" in after
    assert "reviewed_by_user_id" in after
    assert "execution_timeout" in after


def test_upgrade_adds_missing_review_columns():
    """Legacy user_plugins table (pre review-trail) should gain the new columns."""
    engine = create_engine("sqlite:///:memory:")

    # Build a legacy user_plugins table by hand, without any of the
    # columns that were added later.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE user_plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL,
                    description TEXT NOT NULL,
                    "group" VARCHAR(32) NOT NULL,
                    type VARCHAR(32) NOT NULL,
                    author VARCHAR(128) NOT NULL,
                    file_path VARCHAR(512) NOT NULL,
                    rating FLOAT NOT NULL DEFAULT 0.0,
                    approval_status VARCHAR(16) NOT NULL DEFAULT 'pending',
                    user_id INTEGER,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """
            )
        )

    before = _column_names(engine, "user_plugins")
    assert "rejection_reason" not in before
    assert "reviewed_by_user_id" not in before

    run_startup_upgrades(engine)

    after = _column_names(engine, "user_plugins")
    # Every column the schema upgrader knows about is now present.
    for expected in (
        "rejection_reason",
        "reviewed_by_user_id",
        "reviewed_at",
        "execution_timeout",
        "memory_limit",
        "is_public",
        "version",
        "tags",
        "category",
    ):
        assert expected in after, "expected column {} to be present after upgrade".format(expected)


def test_upgrader_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])

    run_startup_upgrades(engine)
    run_startup_upgrades(engine)

    cols = _column_names(engine, "user_plugins")
    assert "rejection_reason" in cols


def test_missing_table_is_ignored():
    """Upgrader must skip silently if the table has not been created yet."""
    engine = create_engine("sqlite:///:memory:")
    run_startup_upgrades(engine)


def test_upgrade_adds_is_admin_to_existing_users_table():
    """Pre-marketplace users table must gain is_admin so User queries don't raise."""
    engine = create_engine("sqlite:///:memory:")

    # Hand-build a pre-marketplace users table (no is_admin, no
    # user_plugins yet). Matches the schema an existing install would
    # have on disk before pulling this branch.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    is_active BOOLEAN,
                    otp_secret_key VARCHAR(255) NOT NULL UNIQUE
                )
                """
            )
        )

    before = _column_names(engine, "users")
    assert "is_admin" not in before

    run_startup_upgrades(engine)

    after = _column_names(engine, "users")
    assert "is_admin" in after

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (name, email, password, is_active, otp_secret_key) "
                "VALUES ('alice', 'a@example.com', 'x', 1, 'k1')"
            )
        )
        row = conn.execute(text("SELECT is_admin FROM users WHERE name='alice'")).fetchone()
    assert row is not None
    # SQLite stores BOOLEAN as 0/1.
    assert row[0] in (0, False)


def test_users_upgrade_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])

    run_startup_upgrades(engine)
    run_startup_upgrades(engine)

    cols = _column_names(engine, "users")
    assert "is_admin" in cols


def test_run_startup_upgrades_is_a_no_op_after_first_call():
    """The module-level guard blocks a second inspection pass in the same process."""
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])

    run_startup_upgrades(engine)
    assert upgrade_module._UPGRADES_APPLIED is True

    # Second call should skip: point the inspector at a broken engine to
    # prove the code path never runs.
    run_startup_upgrades("not-an-engine")


def test_guard_stays_unset_when_upgrade_fails(monkeypatch):
    """A DDL failure must leave the guard False so the next start retries."""
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])

    # Force a real (non-duplicate-column) DBAPI failure on every ALTER.
    def _boom(engine_arg, table_name, upgrades):
        raise OperationalError("ALTER TABLE ...", {}, Exception("disk full"))

    monkeypatch.setattr(upgrade_module, "_add_missing_columns", _boom)

    with pytest.raises(OperationalError):
        run_startup_upgrades(engine)

    assert upgrade_module._UPGRADES_APPLIED is False, (
        "guard must stay False after a failed upgrade so the next start retries"
    )


def test_non_duplicate_ddl_error_is_raised():
    """Only duplicate-column races are swallowed; every other error stops startup."""
    engine = create_engine("sqlite:///:memory:")

    # Create user_plugins with a broken column definition so the first
    # ALTER hits a genuine SQL error rather than a duplicate-column race.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE user_plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL
                )
                """
            )
        )

    # Point the upgrader at a bogus DDL fragment. SQLite raises
    # OperationalError("near ...: syntax error"), which is not a
    # duplicate-column race and must propagate.
    monkeypatch_upgrades = [("garbage_col", "NOT A REAL TYPE ((")]
    original = upgrade_module._USER_PLUGIN_COLUMN_UPGRADES
    upgrade_module._USER_PLUGIN_COLUMN_UPGRADES = monkeypatch_upgrades
    try:
        with pytest.raises(OperationalError):
            run_startup_upgrades(engine)
    finally:
        upgrade_module._USER_PLUGIN_COLUMN_UPGRADES = original

    assert upgrade_module._UPGRADES_APPLIED is False


def test_duplicate_column_race_is_swallowed_and_other_columns_added():
    """A duplicate-column error on one ALTER must not stop the rest of the batch."""
    engine = create_engine("sqlite:///:memory:")

    # Legacy table plus rejection_reason already added by a hypothetical
    # sibling worker. The upgrader will hit "duplicate column" on
    # rejection_reason and must continue with the remaining columns.
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE user_plugins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL,
                    rejection_reason TEXT
                )
                """
            )
        )

    # Rebuild _existing_columns behaviour to omit rejection_reason so
    # the upgrader tries to add it again, triggering the race path.
    original_existing = upgrade_module._existing_columns

    def _pretend_rejection_reason_missing(engine_arg, table_name):
        cols = original_existing(engine_arg, table_name)
        cols.discard("rejection_reason")
        return cols

    upgrade_module._existing_columns = _pretend_rejection_reason_missing
    try:
        run_startup_upgrades(engine)
    finally:
        upgrade_module._existing_columns = original_existing

    cols = _column_names(engine, "user_plugins")
    # The rest of the batch still landed.
    for expected in (
        "reviewed_by_user_id",
        "reviewed_at",
        "execution_timeout",
        "memory_limit",
        "is_public",
        "version",
        "tags",
        "category",
    ):
        assert expected in cols
    # Guard is set because the run succeeded end to end.
    assert upgrade_module._UPGRADES_APPLIED is True


# ---------------------------------------------------------------------------
# PostgreSQL coverage. Skipped unless TEST_POSTGRES_URL is set, e.g.
# TEST_POSTGRES_URL=postgresql+psycopg2://user:pass@localhost:5432/owtf_test
# ---------------------------------------------------------------------------


postgres_only = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="TEST_POSTGRES_URL not set; requires a running PostgreSQL instance",
)


def _drop_test_tables(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS user_plugins CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))


@postgres_only
def test_postgres_upgrade_adds_missing_columns():
    """End-to-end upgrade on a pre-review-trail user_plugins table in PostgreSQL."""
    engine = create_engine(POSTGRES_URL)
    _drop_test_tables(engine)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE user_plugins (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(128) NOT NULL,
                        description TEXT NOT NULL,
                        "group" VARCHAR(32) NOT NULL,
                        type VARCHAR(32) NOT NULL,
                        author VARCHAR(128) NOT NULL,
                        file_path VARCHAR(512) NOT NULL,
                        rating FLOAT NOT NULL DEFAULT 0.0,
                        approval_status VARCHAR(16) NOT NULL DEFAULT 'pending',
                        user_id INTEGER,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                    """
                )
            )

        run_startup_upgrades(engine)

        cols = _column_names(engine, "user_plugins")
        for expected in (
            "rejection_reason",
            "reviewed_by_user_id",
            "reviewed_at",
            "execution_timeout",
            "memory_limit",
            "is_public",
            "version",
            "tags",
            "category",
        ):
            assert expected in cols
    finally:
        _drop_test_tables(engine)


@postgres_only
def test_postgres_partial_upgrade_recovers_after_duplicate_column_error():
    """
    Simulate the race described in _add_missing_columns: one column has
    already been added by a parallel worker. PostgreSQL aborts a whole
    transaction after the first DDL error, so if the loop shared a single
    txn every later ALTER would silently fail. Per-column transactions
    must let the remaining ALTERs succeed.
    """
    engine = create_engine(POSTGRES_URL)
    _drop_test_tables(engine)
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE user_plugins (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(128) NOT NULL,
                        description TEXT NOT NULL,
                        "group" VARCHAR(32) NOT NULL,
                        type VARCHAR(32) NOT NULL,
                        author VARCHAR(128) NOT NULL,
                        file_path VARCHAR(512) NOT NULL,
                        rating FLOAT NOT NULL DEFAULT 0.0,
                        approval_status VARCHAR(16) NOT NULL DEFAULT 'pending',
                        user_id INTEGER,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        rejection_reason TEXT
                    )
                    """
                )
            )

        # rejection_reason already exists; the upgrader will hit a
        # duplicate-column error on that ALTER but must still add every
        # other missing column.
        run_startup_upgrades(engine)

        cols = _column_names(engine, "user_plugins")
        for expected in (
            "reviewed_by_user_id",
            "reviewed_at",
            "execution_timeout",
            "memory_limit",
            "is_public",
            "version",
            "tags",
            "category",
        ):
            assert expected in cols, "expected column {} to be present after upgrade".format(expected)
    finally:
        _drop_test_tables(engine)
