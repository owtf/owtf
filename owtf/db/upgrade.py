"""
owtf.db.upgrade
~~~~~~~~~~~~~~~

Idempotent ALTER TABLE ADD COLUMN runner for tables that gained new
columns after their initial release. Called once at app startup from
owtf.core.main; also guarded so repeat calls in the same process are
a no-op.
"""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

_UPGRADES_APPLIED = False


# Each entry is (column_name, DDL fragment) appended after
# "ADD COLUMN <name>". Types are ANSI so both PostgreSQL and SQLite
# accept them.
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

_USERS_COLUMN_UPGRADES = [
    ("is_admin", "BOOLEAN NOT NULL DEFAULT FALSE"),
]


def _existing_columns(engine, table_name):
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def _add_missing_columns(engine, table_name, upgrades):
    present = _existing_columns(engine, table_name)
    if not present:
        # Table has not been created yet; create_all will build it fresh.
        return

    # One transaction per column. PostgreSQL aborts the whole transaction
    # on the first DDL error, so wrapping the loop in a single txn would
    # silently lose every ALTER after a duplicate-column race.
    for col_name, ddl in upgrades:
        if col_name in present:
            continue
        stmt = "ALTER TABLE {} ADD COLUMN {} {}".format(table_name, col_name, ddl)
        logger.info("Upgrading schema: %s", stmt)
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            logger.warning("Schema upgrade failed for %s.%s: %s", table_name, col_name, exc)


def run_startup_upgrades(engine):
    """Apply every registered ADD COLUMN upgrade. Runs at most once per process."""
    global _UPGRADES_APPLIED
    if _UPGRADES_APPLIED:
        return
    _UPGRADES_APPLIED = True
    _add_missing_columns(engine, "user_plugins", _USER_PLUGIN_COLUMN_UPGRADES)
    _add_missing_columns(engine, "users", _USERS_COLUMN_UPGRADES)
