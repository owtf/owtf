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
'''
#import shlex
from collections import defaultdict
from framework.lib.general import *
import signal
import subprocess
import os
import logging

class Shell(object):
        def __init__(self, Core):
                self.DynamicReplacements = {} # Some settings like the plugin output dir are dynamic, config is no place for those
                self.Core = Core
                #self.CommandInfo = defaultdict(list)
                self.CommandTimeOffset = 'Command'
                self.OldCommands = defaultdict(list)
                # Environment variables for shell
                self.ShellEnviron = os.environ.copy()

        def ShellPathEscape(self, Text):
                return MultipleReplace(Text, { ' ':'\ ', '(':'\(', ')':'\)' }).strip()

        def RefreshReplacements(self):
                self.DynamicReplacements['###PLUGIN_OUTPUT_DIR###'] = self.Core.DB.Target.GetPath('PLUGIN_OUTPUT_DIR')

        def GetModifiedShellCommand(self, Command, PluginOutputDir):
                self.RefreshReplacements()
                NewCommand = "cd "+self.ShellPathEscape(PluginOutputDir)+"; "+MultipleReplace(Command, self.DynamicReplacements)
                self.OldCommands[NewCommand] = Command
                #self.StartCommand(Command, NewCommand)
                return NewCommand

        def StartCommand(self, OriginalCommand, ModifiedCommand):
                #CommandInfo = defaultdict(list)
                if OriginalCommand == ModifiedCommand and ModifiedCommand in self.OldCommands:
                        OriginalCommand = self.OldCommands[ModifiedCommand] # Restore original command saved at modification time
                self.Core.Timer.StartTimer(self.CommandTimeOffset)
                return { 'OriginalCommand' : OriginalCommand, 'ModifiedCommand' : ModifiedCommand, 'Start' : self.Core.Timer.GetStartDateTimeAsStr(self.CommandTimeOffset) }
                #CommandInfo = { 'OriginalCommand' : OriginalCommand, 'ModifiedCommand' : ModifiedCommand, 'Start' : self.Core.Timer.GetStartDateTimeAsStr(self.CommandTimeOffset) } 
                #self.CommandInfo = CommandInfo

        def FinishCommand(self, CommandInfo, WasCancelled):
                CommandInfo['End'] = self.Core.Timer.GetEndDateTimeAsStr(self.CommandTimeOffset)
                Success = True
                if WasCancelled:
                        Success = False
                CommandInfo['Success'] = Success
                CommandInfo['RunTime'] = self.Core.Timer.GetElapsedTimeAsStr(self.CommandTimeOffset)
                CommandInfo['Target'] = self.Core.DB.Target.GetTargetID()
                self.Core.DB.CommandRegister.AddCommand(CommandInfo)
                #self.CommandInfo = defaultdict(list)

        def CanRunCommand(self, Command):
                #Target = self.Core.DB.POutput.CommandAlreadyRegistered(Command['OriginalCommand'])
                #if Target: # Command was run before
                #        if Target == self.Core.Config.Get('TARGET'): # Run several times against same target for grep plugins.  #and self.Core.Config.Get('FORCE_OVERWRITE'):
                #                return [ None, True ] # Can only run again if against the same target and when -f was specified
                #        return [Target, False ]
                #return [ None, True ] # Command was not run before
                Target = self.Core.DB.CommandRegister.CommandAlreadyRegistered(Command['OriginalCommand'])
                if Target: # target_config will be None for a not found match
                    return [Target, False]
                return [None, True]

        def create_subprocess(self, Command):
            # Add proxy settings to environment variables so that tools can pick it up
            # TODO: Uncomment the following lines, when testing has been ensured for using environment variables for proxification,
            # because these variables are set for every command that is run
            # proxy_ip, proxy_port = self.Core.DB.Config.Get("INBOUND_PROXY_IP"), self.Core.DB.Config.Get("INBOUND_PROXY_PORT")
            # self.ShellEnviron["http_proxy"] = "http://" + proxy_ip + ":" + proxy_port
            # self.ShellEnviron["https_proxy"] = "https://" + proxy_ip + ":" + proxy_port

            #http://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612)
            proc = subprocess.Popen(
                Command,
                shell=True,
                env=self.ShellEnviron,
                preexec_fn=os.setsid,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1
            )
            return proc

        def shell_exec_monitor(self, Command):
                #if not self.CommandInfo:
                CommandInfo = self.StartCommand(Command, Command)
                #Target, CanRun = self.CanRunCommand(self.CommandInfo)
                Target, CanRun = self.CanRunCommand(CommandInfo)
                if not CanRun:
                        Message = "The command was already run for target: " + str(Target)
                        return Message
                log("\nExecuting (s to abort THIS COMMAND ONLY):\n"+Command)
                log("")
                log("------> Execution Start Date/Time: "+self.Core.Timer.GetStartDateTimeAsStr('Command'))
                log("")
                Output = ''
                Cancelled = False
                try: # Stolen from: http://stackoverflow.com/questions/5833716/how-to-capture-output-of-a-shell-script-running-in-a-separate-process-in-a-wxpyt
                        proc = self.create_subprocess(Command)
                        while True:
                                line = proc.stdout.readline()
                                if not line: break
                                # NOTE: Below MUST BE print instead of "cprint" to clearly distinguish between owtf output and tool output
                                log(MultipleReplace(line, { "\n":"", "\r":"" })) # Show progress on the screen too!
                                Output += line # Save as much output as possible before a tool crashes! :)
                except KeyboardInterrupt:
                        os.killpg(proc.pid, signal.SIGINT)
                        outdata, errdata = proc.communicate()
                        log(outdata)
                        Output += outdata
                        try:
                            os.kill(proc.pid, signal.SIGTERM) # Plugin KIA (Killed in Action)
                        except OSError:
                            pass # Plugin RIP (Rested In Peace)
                        Cancelled = True
                        #self.FinishCommand(self.CommandInfo, Cancelled)
                        Output += self.Core.Error.UserAbort('Command', Output) # Identify as Command Level abort
                finally:
                        self.FinishCommand(CommandInfo, Cancelled)
                return Output

        def shell_exec(self, Command, **kwds): # Mostly used for internal framework commands
                #Stolen from (added shell=True tweak, necessary for easy piping straight via the command line, etc):
                #http://stackoverflow.com/questions/236737/making-a-system-call-that-returns-the-stdout-output-as-a-string/236909#236909
                kwds.setdefault("stdout", subprocess.PIPE)
                kwds.setdefault("stderr", subprocess.STDOUT)
                p = subprocess.Popen(Command, shell=True, **kwds)
                return p.communicate()[0]
