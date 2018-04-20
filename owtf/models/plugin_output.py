"""
owtf.models.plugin_output
~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property

from owtf.db.model_base import Model


class PluginOutput(Model):
    __tablename__ = "plugin_outputs"

    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    # There is a column named plugin which is caused by backref from the plugin class
    id = Column(Integer, primary_key=True)
    plugin_code = Column(String)  # OWTF Code
    plugin_group = Column(String)
    plugin_type = Column(String)
    date_time = Column(DateTime, default=datetime.datetime.now())
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    output = Column(String, nullable=True)
    error = Column(String, nullable=True)
    status = Column(String, nullable=True)
    user_notes = Column(String, nullable=True)
    user_rank = Column(Integer, nullable=True, default=-1)
    owtf_rank = Column(Integer, nullable=True, default=-1)
    output_path = Column(String, nullable=True)

    @hybrid_property
    def run_time(self):
        return self.end_time - self.start_time

    __table_args__ = (UniqueConstraint('plugin_key', 'target_id'),)
