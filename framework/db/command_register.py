#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
            if register_entry.success and \
                    self.plugin_output.PluginOutputExists(
                        register_entry.plugin_key, register_entry.target_id):
                return self.target.GetTargetURLForID(
                    register_entry.target_id)
            else:  # Either command failed or plugin output doesn't exist
                self.DeleteCommand(original_command)
            return self.target.GetTargetURLForID(register_entry.target)
        return None
