"""
owtf.db.migrations
~~~~~~~~~~~~~~~~~~
Database schema migrations for GSoC 2026 phases.
"""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)


PLUGIN_OUTPUTS_TABLE = "plugin_outputs"
FINGERPRINT_INDEX = "ix_plugin_outputs_fingerprint"


def upgrade_add_fingerprint_column(engine):
    """Add the plugin-output fingerprint column and unique index if needed.

    ``PluginOutput.__tablename__`` is ``plugin_outputs``.  The previous
    migration used the singular name and therefore silently skipped every
    existing OWTF database.
    """
    inspector = inspect(engine)
    if PLUGIN_OUTPUTS_TABLE not in inspector.get_table_names():
        logger.info("%s table does not exist yet; skipping fingerprint migration", PLUGIN_OUTPUTS_TABLE)
        return

    with engine.begin() as conn:
        columns = {column["name"] for column in inspect(conn).get_columns(PLUGIN_OUTPUTS_TABLE)}
        if "fingerprint" not in columns:
            conn.execute(text(f"ALTER TABLE {PLUGIN_OUTPUTS_TABLE} ADD COLUMN fingerprint VARCHAR"))
            logger.info("Fingerprint column added to %s", PLUGIN_OUTPUTS_TABLE)

        conn.execute(
            text(f"CREATE UNIQUE INDEX IF NOT EXISTS {FINGERPRINT_INDEX} ON {PLUGIN_OUTPUTS_TABLE} (fingerprint)")
        )
        logger.info("Fingerprint index verified on %s", PLUGIN_OUTPUTS_TABLE)
