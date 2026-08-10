"""
tests/test_db_upgrade.py
~~~~~~~~~~~~~~~~~~~~~~~~

Verify the schema upgrader that keeps existing installs from crashing
when new columns are added to ``user_plugins``.

Two scenarios have to hold:

1. Fresh install. ``run_startup_upgrades`` runs against an already
   up-to-date table and does nothing. Nothing raises.
2. Upgrade from an older version. We simulate that by hand-creating a
   stripped-down ``user_plugins`` table with only the pre-review
   columns, then calling ``run_startup_upgrades`` and confirming the
   missing columns are added.

Both scenarios use in-memory SQLite so no PostgreSQL is required.
"""

from sqlalchemy import create_engine, inspect, text

# Import only the two models we actually query from. Using
# Model.metadata.create_all(engine, tables=...) below restricts DDL to
# these two tables regardless of what other test modules have
# registered on the shared metadata — otherwise a sibling test that
# imports plugin_output / work would drag their unresolved FK targets
# into our create_all and blow up.
import owtf.models.email_confirmation  # noqa: F401
import owtf.models.user  # noqa: F401
import owtf.models.user_login_token  # noqa: F401
from owtf.db.upgrade import run_startup_upgrades
from owtf.models.user import User
from owtf.models.user_plugin import UserPlugin


def _column_names(engine, table):
    return {c["name"] for c in inspect(engine).get_columns(table)}


def test_fresh_install_is_a_no_op():
    """A freshly created schema already has every column. The upgrader
    must run without error and leave the columns exactly as they were.
    """
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
    """Simulate an operator who checked out an older version of this
    branch (pre-review-trail) and is now pulling the latest. Their
    ``user_plugins`` table has the original columns only. After the
    upgrader runs, every column the ORM expects must be present.
    """
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
    """Calling run_startup_upgrades twice in a row must not raise. The
    second call should see every column already present and skip
    every ALTER statement."""
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])

    run_startup_upgrades(engine)
    run_startup_upgrades(engine)  # Must be a no-op.

    cols = _column_names(engine, "user_plugins")
    assert "rejection_reason" in cols


def test_missing_table_is_ignored():
    """If the table has not been created at all (a scenario where a
    developer wipes the DB but forgets to import the model), the
    upgrader must silently skip instead of crashing."""
    engine = create_engine("sqlite:///:memory:")
    # No create_all; user_plugins table simply does not exist.

    # Should not raise.
    run_startup_upgrades(engine)


def test_upgrade_adds_is_admin_to_existing_users_table():
    """Simulate an operator upgrading to the marketplace release. Their
    users table predates the marketplace and has no is_admin column, so
    the very first User query would raise UndefinedColumn on boot unless
    the upgrader adds the column. This is the regression viyatb flagged
    in the review of PR #1444.
    """
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
    assert "is_admin" in after, "is_admin column must be added on upgrade"

    # Confirm the ORM can now issue a plain User query without hitting
    # UndefinedColumn. This is the actual failure mode we are guarding
    # against: any endpoint that touches User.is_admin blows up otherwise.
    with engine.begin() as conn:
        # A row with is_admin defaulted to FALSE.
        conn.execute(
            text(
                "INSERT INTO users (name, email, password, is_active, otp_secret_key) "
                "VALUES ('alice', 'a@example.com', 'x', 1, 'k1')"
            )
        )
        row = conn.execute(text("SELECT is_admin FROM users WHERE name='alice'")).fetchone()
    assert row is not None
    # SQLite stores BOOLEAN as 0/1; both False and 0 mean the same thing here.
    assert row[0] in (0, False)


def test_users_upgrade_is_idempotent():
    """Running the upgrader twice against a users table that already has
    is_admin must be a no-op and must not raise."""
    engine = create_engine("sqlite:///:memory:")
    UserPlugin.metadata.create_all(engine, tables=[User.__table__, UserPlugin.__table__])

    run_startup_upgrades(engine)
    run_startup_upgrades(engine)

    cols = _column_names(engine, "users")
    assert "is_admin" in cols
