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

The shell module allows running arbitrary shell commands and is critical to the framework in order to run third party tools
The interactive shell module allows non-blocking interaction with subprocesses running tools or remote connections (i.e. shells)
'''
# import shlex
import subprocess
from framework.lib.general import *
from framework.shell import blocking_shell
from framework.shell.async_subprocess import *
from collections import defaultdict


class InteractiveShell(blocking_shell.Shell):

    COMPONENT_NAME = "interactive_shell"

    def __init__(self, Core):
        blocking_shell.Shell.__init__(self, Core)  # Calling parent class to do its init part
        self.register_in_service_locator()
        self.Connection = None
        self.Options = None
        self.CommandTimeOffset = 'InteractiveCommand'

    def CheckConnection(self, AbortMessage):
        if not self.Connection:
            cprint("ERROR - Communication channel closed - " + AbortMessage)
            return False
        return True

    def Read(self, Time=1):
        Output = ''
        if not self.CheckConnection('Cannot read'):
            return Output
        try:
            Output = RecvSome(self.Connection, Time)
        except DisconnectException:
            cprint("ERROR: Read - The Communication channel is down!")
            return Output  # End of communication channel
        print Output  # Show progress on screen
        return Output

    def FormatCommand(self, Command):
        #print "self.Options['RHOST']=" + str(self.Options['RHOST']) + "self.Options['RPORT']=" + str(self.Options['RPORT']) + "Command=" + str(Command)
        if "RHOST" in self.Options and 'RPORT' in self.Options:  # Interactive shell on remote connection
            return self.Options['RHOST'] + ':' + self.Options['RPORT'] + ' - ' + Command
        else:
            return "Interactive - " + Command

    def Run(self, Command):
        Output = ''
        Cancelled = False
        if not self.CheckConnection("NOT RUNNING Interactive command: " + Command):
            return Output
        # TODO: tail to be configurable: \n for *nix, \r\n for win32
        LogCommand = self.FormatCommand(Command)
        CommandInfo = self.StartCommand(LogCommand, LogCommand)
        try:
            cprint("Running Interactive command: " + Command)
            SendAll(self.Connection, Command + "\n")
            Output += self.Read()
            self.FinishCommand(CommandInfo, Cancelled)
        except DisconnectException:
            Cancelled = True
            cprint("ERROR: Run - The Communication Channel is down!")
            self.FinishCommand(CommandInfo, Cancelled)
        except KeyboardInterrupt:
            Cancelled = True
            self.FinishCommand(CommandInfo, Cancelled)
            Output += self.error_handler.UserAbort('Command', Output)  # Identify as Command Level abort
        if not Cancelled:
            self.FinishCommand(CommandInfo, Cancelled)
        return Output

    def RunCommandList(self, CommandList):
        Output = ""
        for Command in CommandList:
            Output += self.Run(Command)
        return Output

    def Open(self, Options, PluginInfo):
        Output = ''
        if not self.Connection:
            Name, Command = Options['ConnectVia'][0]
            self.Connection = AsyncPopen(Command, shell=True,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         stdin=subprocess.PIPE,
                                         bufsize=1)
            if Options['InitialCommands']:
                Output += self.RunCommandList(Options['InitialCommands'])
            self.Options = Options  # Store Options for Closing processing
            Output += self.Read()
        Output += self.Read()
        return Output

    def Close(self, PluginInfo):
        print "wtf Close: " + str(self.Options)
        if self.Options['CommandsBeforeExit']:
            cprint("Running commands before closing Communication Channel..")
            self.RunCommandList(self.Options['CommandsBeforeExit'].split(self.Options['CommandsBeforeExitDelim']))
        #self.RunCommandList(self.Options['CommandsBeforeExit'].split('#'))
        cprint("Trying to close Communication Channel..")
        self.Run("exit")

        if self.Options['ExitMethod'] == 'kill':
            cprint("Killing Communication Channel..")
            self.Connection.kill()
        else:  # By default wait
            cprint("Waiting for Communication Channel to close..")
            self.Connection.wait()
        #self.Read()
        self.Connection = None

    #self.Connection.stdin = "exit\r"
    #self.Connection.wait()
    #self.Connection.kill()
    #return Core.PluginHelper.DrawCommandDump('Init Channel Command', 'Output', Core.Config.GetResources(Resource), PluginInfo, "") # No previous output

    def IsClosed(self):
        return self.Connection == None