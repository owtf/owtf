"""
owtf.db.upgrade
~~~~~~~~~~~~~~~

Lightweight schema upgrader for tables that gained new columns in a
release.

OWTF has never used Alembic. New installs get their schema from
``Model.metadata.create_all(engine)``, which creates missing *tables*
but never adds missing *columns* to an existing table. That means an
operator who upgrades an existing OWTF install to a version that added
columns will hit ``UndefinedColumn`` errors at runtime.

This module fills that gap. It inspects a table's live columns, and
runs ``ALTER TABLE ADD COLUMN`` for anything the ORM model expects that
is not there yet. It is idempotent, so it is safe to call on every
engine startup.

Scope: only tables that have actually gained columns get an entry
here. The goal is a small, auditable list of upgrades, not a
general-purpose migration framework. If the schema churn grows past a
handful of tables, switch to Alembic.
"""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)


# One entry per column added after the table's initial release.
# Each row is (column_name, DDL fragment) where the DDL fragment is
# everything after ``ADD COLUMN <name>``. Types are ANSI-ish so both
# PostgreSQL (production) and SQLite (tests) accept them.
_USER_PLUGIN_COLUMN_UPGRADES = [
    ("rejection_reason", "TEXT"),
    ("reviewed_by_user_id", "INTEGER"),
    ("reviewed_at", "TIMESTAMP"),
    ("execution_timeout", "INTEGER NOT NULL DEFAULT 300"),
    ("memory_limit", "INTEGER NOT NULL DEFAULT 268435456"),
    ("is_public", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("version", "VARCHAR(32) NOT NULL DEFAULT '1.0.0'"),
    ("tags", "VARCHAR(256)"),
    ("category", "VARCHAR(64)"),
]

# users.is_admin was added for the community plugin marketplace. Existing
# installs already have a users table, so create_all will not add the new
# column and any User query would blow up with UndefinedColumn on boot.
_USERS_COLUMN_UPGRADES = [
    ("is_admin", "BOOLEAN NOT NULL DEFAULT FALSE"),
]


def _existing_columns(engine, table_name):
    """Return the set of column names present on *table_name*, or an
    empty set if the table itself does not exist yet."""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        # Table has not been created yet. create_all will handle it
        # with the current model definition, so there is nothing to
        # ALTER.
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def _add_missing_columns(engine, table_name, upgrades):
    """Run ``ALTER TABLE ADD COLUMN`` for any column in *upgrades* that
    is not already on the table."""
    present = _existing_columns(engine, table_name)
    if not present:
        return  # Nothing to upgrade — table will be created fresh.

    with engine.begin() as conn:
        for col_name, ddl in upgrades:
            if col_name in present:
                continue
            stmt = "ALTER TABLE {} ADD COLUMN {} {}".format(table_name, col_name, ddl)
            logger.info("Upgrading schema: %s", stmt)
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                # A single failing column should not stop the rest.
                # Most commonly this is a race with a parallel worker
                # that already added the column, or a dialect that
                # rejects the default clause. Log loudly and continue.
                logger.warning("Schema upgrade failed for %s.%s: %s", table_name, col_name, exc)


def run_startup_upgrades(engine):
    """Apply every registered ADD COLUMN upgrade.

    Called from :func:`owtf.db.session.get_db_engine` right after
    ``create_all``. Safe to call repeatedly.
    """
    _add_missing_columns(engine, "user_plugins", _USER_PLUGIN_COLUMN_UPGRADES)
    _add_missing_columns(engine, "users", _USERS_COLUMN_UPGRADES)
