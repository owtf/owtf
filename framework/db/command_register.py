#!/usr/bin/env python
'''
Component to handle data storage and search of all commands run
'''
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import CommandRegisterInterface

from framework.lib.general import cprint
from framework.db import models
from framework.db.target_manager import target_required

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

    def AddCommand(self, Command):
        self.db.session.merge(models.Command(
            start_time=Command['Start'],
            end_time=Command['End'],
            success=Command['Success'],
            target_id=Command['Target'],
            plugin_key=Command['PluginKey'],
            modified_command=Command['ModifiedCommand'].strip(),
            original_command=Command['OriginalCommand'].strip()
        ))
        self.db.session.commit()

    def DeleteCommand(self, Command):
        command_obj = self.db.session.query(models.Command).get(Command)
        self.db.session.delete(command_obj)
        self.db.session.commit()

    @target_required
    def CommandAlreadyRegistered(self, original_command, target_id=None):
        register_entry = self.db.session.query(models.Command).get(original_command)
        if register_entry:
            # If the command was completed and the plugin output to which it
            # is referring exists
            if register_entry.success and self.plugin_output.PluginOutputExists(register_entry.plugin_key, register_entry.target_id):
                return self.target.GetTargetURLForID(register_entry.target_id)
            else:  # Either command failed or plugin output doesn't exist
                self.DeleteCommand(original_command)
                return self.target.GetTargetURLForID(register_entry.target_id)
        return None
