"""
owtf.models.plugin_execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Persistent records for plugin executions.  Unlike the in-memory metrics
collector, this table is shared by all OWTF worker processes.
"""

from sqlalchemy import Column, DateTime, Integer, String

from owtf.db.model_base import Model


class PluginExecution(Model):
    """One persisted plugin execution event."""

    __tablename__ = "plugin_executions"

    id = Column(Integer, primary_key=True)
    plugin_key = Column(String, nullable=False, index=True)
    plugin_code = Column(String, nullable=False, index=True)
    plugin_group = Column(String, nullable=False)
    plugin_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
