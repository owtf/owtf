"""
owtf.db.upgrade
~~~~~~~~~~~~~~~

Idempotent ALTER TABLE ADD COLUMN runner for tables that gained new
columns after their initial release. OWTF does not use Alembic, and
``create_all`` never adds columns to an existing table, so upgraded
installs would otherwise crash with UndefinedColumn on the first
query.
"""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)


# Each entry is (column_name, DDL fragment) appended after
# "ADD COLUMN <name>". Types are ANSI so both PostgreSQL and SQLite
# accept them.
_USER_PLUGIN_COLUMN_UPGRADES = [
    ("rejection_reason", "TEXT"),
    ("reviewed_by_user_id", "INTEGER"),
    ("reviewed_at", "TIMESTAMP"),
    ("execution_timeout", "INTEGER NOT NULL DEFAULT 300"),
    ("is_public", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("version", "VARCHAR(32) NOT NULL DEFAULT '1.0.0'"),
    ("tags", "VARCHAR(256)"),
    ("category", "VARCHAR(64)"),
]

_USERS_COLUMN_UPGRADES = [
    ("is_admin", "BOOLEAN NOT NULL DEFAULT FALSE"),
]

# execution_timeout on the built-in plugins table is set only on the
# community-plugin mirror rows; built-in plugins leave it NULL. This
# lets Plugin.to_dict() carry the timeout through _derive_work_dict
# into the runner unchanged.
_PLUGINS_COLUMN_UPGRADES = [
    ("source", "VARCHAR(32)"),
    ("file_path", "VARCHAR(512)"),
    ("execution_timeout", "INTEGER"),
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

    with engine.begin() as conn:
        for col_name, ddl in upgrades:
            if col_name in present:
                continue
            stmt = "ALTER TABLE {} ADD COLUMN {} {}".format(table_name, col_name, ddl)
            logger.info("Upgrading schema: %s", stmt)
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                # Do not let one failing column stop the rest. Most often this
                # is a race with a parallel worker that already added it.
                logger.warning("Schema upgrade failed for %s.%s: %s", table_name, col_name, exc)


def run_startup_upgrades(engine):
    """Apply every registered ADD COLUMN upgrade. Idempotent."""
    _add_missing_columns(engine, "user_plugins", _USER_PLUGIN_COLUMN_UPGRADES)
    _add_missing_columns(engine, "users", _USERS_COLUMN_UPGRADES)
    _add_missing_columns(engine, "plugins", _PLUGINS_COLUMN_UPGRADES)
