"""
owtf.models.command
~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.hybrid import hybrid_property

from owtf.db.model_base import Model
from owtf.db.session import flush_transaction
from owtf.models import plugin


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

    @classmethod
    def add_cmd(cls, session, command):
        """Adds a command to the DB"""
        cmd = cls(
            start_time=command["Start"],
            end_time=command["End"],
            success=command["Success"],
            target_id=command["Target"],
            plugin_key=command["PluginKey"],
            modified_command=command["ModifiedCommand"].strip(),
            original_command=command["OriginalCommand"].strip(),
        )
        session.add(cmd)
        session.commit()

    @classmethod
    def delete_cmd(cls, session, command):
        """Delete the command from the DB"""
        command_obj = session.query(Command).get(command)
        session.delete(command_obj)
        session.commit()
