"""
owtf.db.migrations
~~~~~~~~~~~~~~~~~~
Database schema migrations for GSoC 2026 phases.
"""
import logging

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


def upgrade_add_fingerprint_column(engine):
    """Add fingerprint column to plugin_output table if it doesn't exist."""
    with engine.begin() as conn:
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            
            # Check if plugin_output table exists first
            tables = inspector.get_table_names()
            if 'plugin_output' not in tables:
                logger.info("plugin_output table does not exist yet, skipping fingerprint migration")
                return
            
            # Check if fingerprint column already exists
            columns = [col['name'] for col in inspector.get_columns('plugin_output')]
            if 'fingerprint' not in columns:
                conn.execute(text(
                    "ALTER TABLE plugin_output ADD COLUMN fingerprint VARCHAR"
                ))
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_plugin_output_fingerprint ON plugin_output(fingerprint)"
                ))
                logger.info("Fingerprint column and index added to plugin_output table")
            else:
                logger.info("Fingerprint column already exists on plugin_output table")
        except (ProgrammingError, OperationalError) as e:
            logger.exception("Could not add fingerprint column due to database error")
            raise
        except Exception as e:
            logger.exception("Unexpected error during fingerprint column migration")
            raise