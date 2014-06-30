#!/usr/bin/env python
"""

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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The shell module allows running arbitrary shell commands and is critical to the
framework in order to run third party tools.

"""

import subprocess
from collections import defaultdict

from framework.lib.general import *


class Shell(object):
    def __init__(self, Core):
        # Some settings like the plugin output dir are dynamic, config is no
        # place for those.
        self.DynamicReplacements = {}
        self.Core = Core
        self.CommandInfo = defaultdict(list)

    def ShellPathEscape(self, Text):
        return MultipleReplace(Text, { ' ':'\ ', '(':'\(', ')':'\)' }).strip()

    def RefreshReplacements(self):
        self.DynamicReplacements['###PLUGIN_OUTPUT_DIR###'] = self.Core.Config.Get('PLUGIN_OUTPUT_DIR')

    def GetModifiedShellCommand(self, Command, PluginOutputDir):
        self.RefreshReplacements()
        NewCommand = "cd " + self.ShellPathEscape(PluginOutputDir)
        NewCommand += "; " + MultipleReplace(Command, self.DynamicReplacements)
        self.StartCommand(Command, NewCommand)
        return NewCommand

    def StartCommand(self, OriginalCommand, ModifiedCommand):
        CommandInfo = defaultdict(list)
        self.Core.Timer.StartTimer('Command')
        CommandInfo = {
            'OriginalCommand': OriginalCommand,
            'ModifiedCommand': ModifiedCommand,
            'Start': self.Core.Timer.GetStartDateTimeAsStr('Command')}
        self.CommandInfo = CommandInfo

    def FinishCommand(self, CommandInfo, WasCancelled):
        CommandInfo['End'] = self.Core.Timer.GetEndDateTimeAsStr('Command')
        Status = "Finished"
        if WasCancelled:
            Status = "Cancelled"
        CommandInfo['Status'] = Status
        CommandInfo['RunTime'] = self.Core.Timer.GetElapsedTimeAsStr('Command')
        CommandInfo['Target'] = self.Core.Config.Get('TARGET')
        self.Core.DB.CommandRegister.Add(CommandInfo)
        self.CommandInfo = defaultdict(list)

    def CanRunCommand(self, Command):
        Target = self.Core.DB.CommandRegister.AlreadyRegistered(
            Command['OriginalCommand'])
        if Target:  # Command was run before.
            # Run several times against same target for grep plugins.
            if Target == self.Core.Config.Get('TARGET'):
                # Can only run again if against the same target and when -f was
                # specified.
                return [None, True]
            return [Target, False]
        return [None, True]  # Command was not run before.

    def shell_exec_monitor(self, Command):
        if not self.CommandInfo:
            self.StartCommand(Command, Command)
        Target, CanRun = self.CanRunCommand(self.CommandInfo)
        if not CanRun:
            Message = "The command was already run for target: "+Target
            return Message
        cprint(
            "\nExecuting (Control+C to abort THIS COMMAND ONLY):\n" + Command)
        cprint("")
        cprint(
            "------> Execution Start Date/Time: " +
            self.Core.Timer.GetStartDateTimeAsStr('Command'))
        cprint("")
        Output = ''
        Cancelled = False
        # Stolen from:
        # http://stackoverflow.com/questions/5833716/how-to-capture-output-of-a-shell-script-running-in-a-separate-process-in-a-wxpyt
        try:
            proc = subprocess.Popen(
                Command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1)
                while True:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    # NOTE: Below MUST BE print instead of "cprint" to clearly
                    # distinguish between owtf output and tool output.
                    # Show progress on the screen too!
                    print MultipleReplace(line, { "\n":"", "\r":"" })
                    # Save as much output as possible before a tool crashes! :)
                    Output += line
        except KeyboardInterrupt:
            Cancelled = True
            self.FinishCommand(self.CommandInfo, Cancelled)
            # Identify as Command Level abort.
            Output += self.Core.Error.UserAbort('Command', Output)
        if not Cancelled:
            self.FinishCommand(self.CommandInfo, Cancelled)
        return Output

    # Mostly used for internal framework commands.
    def shell_exec(self, Command, **kwds):
        # Stolen from (added shell=True tweak, necessary for easy piping
        # straight via the command line, etc):
        # http://stackoverflow.com/questions/236737/making-a-system-call-that-returns-the-stdout-output-as-a-string/236909#236909
        kwds.setdefault("stdout", subprocess.PIPE)
        kwds.setdefault("stderr", subprocess.STDOUT)
        p = subprocess.Popen(Command, shell=True, **kwds)
        return p.communicate()[0]
