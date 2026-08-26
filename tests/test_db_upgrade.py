"""Tests for the startup schema upgrader (in-memory SQLite)."""

from sqlalchemy import create_engine, inspect, text

# Importing these models registers them on the shared metadata so
# create_all(tables=[...]) can resolve their foreign keys without
# pulling in unrelated tables.
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.db.upgrade import run_startup_upgrades
from owtf.models.user import User
from owtf.models.user_plugin import UserPlugin


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
