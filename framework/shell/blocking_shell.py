#!/usr/bin/env python
'''
The shell module allows running arbitrary shell commands and is critical to the framework in order to run third party tools
'''

from collections import defaultdict
import signal
import subprocess
import os
import sys
import logging

from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import ShellInterface
from framework.lib.general import *
from framework.lib.formatters import LOG_LEVEL_TOOL


class Shell(BaseComponent, ShellInterface):

    COMPONENT_NAME = "shell"

    def __init__(self):
        self.register_in_service_locator()
        # Some settings like the plugin output dir are dynamic, config is no place for those
        self.DynamicReplacements = {}  
        self.command_register = self.get_component("command_register")
        self.target = self.get_component("target")
        self.error_handler = self.get_component("error_handler")
        self.timer = self.get_component("timer")
        self.CommandTimeOffset = 'Command'
        self.OldCommands = defaultdict(list)
        # Environment variables for shell
        self.ShellEnviron = os.environ.copy()

    def RefreshReplacements(self):
        self.DynamicReplacements['###plugin_output_dir###'] = self.target.GetPath('plugin_output_dir')

    def StartCommand(self, OriginalCommand, ModifiedCommand):
        if OriginalCommand == ModifiedCommand and ModifiedCommand in self.OldCommands:
            # Restore original command saved at modification time
            OriginalCommand = self.OldCommands[ModifiedCommand] 
            self.timer.start_timer(self.CommandTimeOffset)
            return {'OriginalCommand': OriginalCommand, 
                    'ModifiedCommand': ModifiedCommand, 
                    'Start': self.timer.get_start_date_time(self.CommandTimeOffset)}

    def FinishCommand(self, CommandInfo, WasCancelled, PluginInfo):
        CommandInfo['End'] = self.timer.get_end_date_time(self.CommandTimeOffset)
        Success = True
        if WasCancelled:
            Success = False
        CommandInfo['Success'] = Success
        CommandInfo['RunTime'] = self.timer.get_elapsed_time_as_str(self.CommandTimeOffset)
        CommandInfo['Target'] = self.target.GetTargetID()
        CommandInfo['PluginKey'] = PluginInfo["key"]
        self.command_register.AddCommand(CommandInfo)

    def ShellPathEscape(self, Text):
        return MultipleReplace(Text, {' ': '\ ', '(': '\(', ')': '\)'})

    def GetModifiedShellCommand(self, Command, PluginOutputDir):
        self.RefreshReplacements()
        NewCommand = "cd %s;%s" % (self.ShellPathEscape(PluginOutputDir), 
            MultipleReplace(Command, self.DynamicReplacements))
        self.OldCommands[NewCommand] = Command
        return NewCommand

    def CanRunCommand(self, Command):
        Target = self.command_register.CommandAlreadyRegistered(Command['OriginalCommand'])
        if Target:  # target_config will be None for a not found match
            return [Target, False]
        return [None, True]

    def create_subprocess(self, Command):
        # Add proxy settings to environment variables so that tools can pick it up
        # TODO: Uncomment the following lines, when testing has been ensured for using environment variables for 
        # proxification, because these variables are set for every command that is run
        # http://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612)
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

    def shell_exec_monitor(self, Command, PluginInfo):
        CommandInfo = self.StartCommand(Command, Command)
        Target, CanRun = self.CanRunCommand(CommandInfo)
        if not CanRun:
            Message = "The command was already run for target: %s" % str(Target)
            return Message
        logging.info("")
        logging.info("Executing :\n\n%s\n\n", Command)
        logging.info("")
        logging.info("------> Execution Start Date/Time: %s" % self.timer.get_start_date_time_as_str('Command'))
        logging.info("")
        Output = ''
        Cancelled = False

        # Stolen from: http://stackoverflow.com/questions/5833716/how-to-capture-output-of-a-shell-script-running-
        # in-a-separate-process-in-a-wxpyt
        try:  
            proc = self.create_subprocess(Command)
            while True:
                line = proc.stdout.readline()
                if not line: 
                    break
                # NOTE: Below MUST BE print instead of "cprint" to clearly distinguish between owtf output and tool output
                logging.warn(line.strip())  # Show progress on the screen too!
                Output += line  # Save as much output as possible before a tool crashes! :)
        except KeyboardInterrupt:
            os.killpg(proc.pid, signal.SIGINT)
            outdata, errdata = proc.communicate()
            logging.warn(outdata)
            Output += outdata
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # Plugin KIA (Killed in Action)
            except OSError:
                pass  # Plugin RIP (Rested In Peace)
            Cancelled = True
            Output += self.error_handler.UserAbort('Command', Output)  # Identify as Command Level abort
        finally:
            self.FinishCommand(CommandInfo, Cancelled, PluginInfo)

        return scrub_output(Output)

    def shell_exec(self, Command, **kwds):  # Mostly used for internal framework commands
        # Stolen from (added shell=True tweak, necessary for easy piping straight via the command line, etc):
        # http://stackoverflow.com/questions/236737/making-a-system-call-that-returns-the-stdout-output-as-a-string/
        # 236909#236909
        kwds.setdefault("stdout", subprocess.PIPE)
        kwds.setdefault("stderr", subprocess.STDOUT)
        p = subprocess.Popen(Command, shell=True, **kwds)
        return p.communicate()[0]
