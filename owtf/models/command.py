"""
owtf.models.command
~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.hybrid import hybrid_property

from owtf.db.model_base import Model


class Command(Model):
    __tablename__ = "command_register"

    start_time = Column(DateTime)
    end_time = Column(DateTime)
    success = Column(Boolean, default=False)
    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    modified_command = Column(String)
    original_command = Column(String, primary_key=True)

    @hybrid_property
    def run_time(self):
        return self.end_time - self.start_time
