"""
owtf.db.command_register
~~~~~~~~~~~~~~~~~~~~~~~~

Component to handle data storage and search of all commands run
"""

from sqlalchemy.exc import SQLAlchemyError

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import CommandRegisterInterface
from owtf.db import models
from owtf.managers.target import target_required


class CommandRegister(BaseComponent, CommandRegisterInterface):

    COMPONENT_NAME = "command_register"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db = self.get_component("db")
        self.plugin_output = None
        self.target = None

    def init(self):
        self.target = self.get_component("target")
        self.plugin_output = self.get_component("plugin_output")

    def add_command(self, command):
        """Adds a command to the DB

        :param command: Command to add
        :type command: `dict`
        :return: None
        :rtype: None
        """
        self.db.session.merge(models.Command(
            start_time=command['Start'],
            end_time=command['End'],
            success=command['Success'],
            target_id=command['Target'],
            plugin_key=command['PluginKey'],
            modified_command=command['ModifiedCommand'].strip(),
            original_command=command['OriginalCommand'].strip()
        ))
        try:
            self.db.session.commit()
        except SQLAlchemyError as e:
            self.db.session.rollback()
            raise e

    def del_command(self, command):
        """Delete the command from the DB

        :param command: Command to delete
        :type command: `dict`
        :return: None
        :rtype: None
        """
        command_obj = self.db.session.query(models.Command).get(command)
        self.db.session.delete(command_obj)
        self.db.session.commit()

    @target_required
    def command_already_registered(self, original_command, target_id=None):
        """Checks if the command has already been registered

        :param original_command: Original command to check
        :type original_command: `dict`
        :param target_id: Target ID
        :type target_id: `int`
        :return: None
        :rtype: None
        """
        register_entry = self.db.session.query(models.Command).get(original_command)
        if register_entry:
            # If the command was completed and the plugin output to which it
            # is referring exists
            if register_entry.success:
                if self.plugin_output.plugin_output_exists(register_entry.plugin_key, register_entry.target_id):
                    return self.target.get_target_url_for_id(register_entry.target_id)
                else:
                    self.del_command(original_command)
                    return None
            else:  # Command failed
                self.del_command(original_command)
                return self.target.get_target_url_for_id(register_entry.target_id)
        return None
