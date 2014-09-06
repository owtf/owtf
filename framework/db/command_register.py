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

from framework.lib.general import cprint
from framework.db import models
from framework.db.target_manager import target_required

class CommandRegister(object):
    def __init__(self, Core):
        self.Core = Core

    def AddCommand(self, Command):
        self.Core.DB.session.merge(models.Command(
            start_time=Command['Start'],
            end_time=Command['End'],
            success=Command['Success'],
            target_id=Command['Target'],
            modified_command=Command['ModifiedCommand'].strip(),
            original_command=Command['OriginalCommand'].strip()
        ))
        self.Core.DB.session.commit()

    def DeleteCommand(self, Command):
        command_obj = self.Core.DB.session.query(models.Command).get(Command)
        self.Core.DB.session.delete(command_obj)
        self.Core.DB.session.commit()

    @target_required
    def CommandAlreadyRegistered(self, original_command, target_id=None):
        register_entry = self.Core.DB.session.query(models.Command).get(original_command)
        if register_entry and register_entry.success:
            if register_entry.success:
                self.DeleteCommand(original_command)
            return self.Core.DB.Target.GetTargetURLForID(
                register_entry.target_id)
        return None
