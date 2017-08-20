"""
owtf.shell.blocking_shell
~~~~~~~~~~~~~~~~~~~~~~~~~

The shell module allows running arbitrary shell commands and is critical to the framework
in order to run third party tools
"""

import signal
import subprocess
import logging

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import ShellInterface
from owtf.lib.general import *
from sqlalchemy.exc import SQLAlchemyError


class Shell(BaseComponent, ShellInterface):

    COMPONENT_NAME = "shell"

    def __init__(self):
        self.register_in_service_locator()
        # Some settings like the plugin output dir are dynamic, config is no place for those
        self.dynamic_replacements = {}
        self.command_register = self.get_component("command_register")
        self.target = self.get_component("target")
        self.error_handler = self.get_component("error_handler")
        self.timer = self.get_component("timer")
        self.command_time_offset = 'Command'
        self.old_cmds = defaultdict(list)
        # Environment variables for shell
        self.shell_env = os.environ.copy()

    def refresh_replacements(self):
        """Refresh the replaced items in the list

        :return: None
        :rtype: None
        """
        self.dynamic_replacements['###plugin_output_dir###'] = self.target.GetPath('plugin_output_dir')

    def start_cmd(self, original_cmd, modified_cmd):
        """Start the timer and return the list of commands to run

        :param original_cmd: Original command
        :type original_cmd: `str`
        :param modified_cmd: Modified command to run
        :type modified_cmd: `str`
        :return: Dict of commands and start time
        :rtype: `dict`
        """
        if original_cmd == modified_cmd and modified_cmd in self.old_cmds:
            # Restore original command saved at modification time
            original_cmd = self.old_cmds[modified_cmd]
        self.timer.start_timer(self.command_time_offset)
        commands = {
            'OriginalCommand': original_cmd,
            'ModifiedCommand': modified_cmd,
            'Start': self.timer.get_start_date_time(self.command_time_offset)
        }
        return commands

    def finish_cmd(self, cmd_info, was_cancelled, plugin_info):
        """Finish the command run

        :param cmd_info: Command info dict
        :type cmd_info: `dict`
        :param was_cancelled: If cancelled by user, then true
        :type was_cancelled: `bool`
        :param plugin_info: Plugin context information
        :type plugin_info: `dict`
        :return: None
        :rtype: None
        """
        cmd_info['End'] = self.timer.get_end_date_time(self.command_time_offset)
        success = True
        if was_cancelled:
            success = False
        cmd_info['Success'] = success
        cmd_info['RunTime'] = self.timer.get_elapsed_time_as_str(self.command_time_offset)
        cmd_info['Target'] = self.target.GetTargetID()
        cmd_info['PluginKey'] = plugin_info["key"]
        self.command_register.AddCommand(cmd_info)

    def escape_shell_path(self, text):
        """Escape shell path characters in the text

        :param text: text to be escaped
        :type text: `str`
        :return: Modified text
        :rtype: `str`
        """
        return multi_replace(Text, {' ': '\ ', '(': '\(', ')': '\)'})

    def get_modified_shell_cmd(self, command, plugin_output_dir):
        """Returns the modified shell command to run

        :param command: Command to run
        :type command: `str`
        :param plugin_output_dir: Path to the plugin output directory
        :type plugin_output_dir: `str`
        :return: Modified command
        :rtype: `str`
        """
        self.refresh_replacements()
        new_cmd = "cd %s;%s" % (self.escape_shell_path(plugin_output_dir),
                                   multi_replace(command, self.dynamic_replacements))
        self.old_cmds[new_cmd] = command
        return new_cmd

    def can_run_cmd(self, command):
        """Check if command is already in place to run

        :param command: Command dict to check
        :type command: `dict`
        :return: List of return values
        :rtype: `list`
        """
        target = self.command_register.CommandAlreadyRegistered(command['OriginalCommand'])
        if target:  # target_config will be None for a not found match
            return [target, False]
        return [None, True]

    def create_subprocess(self, command):
        """Create a subprocess for the command to run

        :param command: Command to run
        :type command: `str`
        :return:
        :rtype:
        """
        # Add proxy settings to environment variables so that tools can pick it up
        # TODO: Uncomment the following lines, when testing has been ensured for using environment variables for
        # proxification, because these variables are set for every command that is run
        # http://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612)
        proc = subprocess.Popen(
            command,
            shell=True,
            env=self.shell_env,
            preexec_fn=os.setsid,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1
        )
        return proc

    def shell_exec_monitor(self, command, plugin_info):
        """Monitor shell command execution

        :param command: Command to run
        :type command: `str`
        :param plugin_info: Plugin context info
        :type plugin_info: `dict`
        :return: Scrubbed output from the command
        :rtype: `str`
        """
        cmd_info = self.start_cmd(command, command)
        target, can_run = self.can_run_cmd(cmd_info)
        if not can_run:
            message = "The command was already run for target: %s" % str(target)
            return message
        logging.info("")
        logging.info("Executing :\n\n%s\n\n", command)
        logging.info("")
        logging.info("------> Execution Start Date/Time: %s" % self.timer.get_start_date_time_as_str('Command'))
        logging.info("")
        output = ''
        cancelled = False

        # Stolen from: http://stackoverflow.com/questions/5833716/how-to-capture-output-of-a-shell-script-running-
        # in-a-separate-process-in-a-wxpyt
        try:
            proc = self.create_subprocess(command)
            while True:
                line = proc.stdout.readline()
                if not line:
                    break
                # NOTE: Below MUST BE print instead of "cprint" to clearly distinguish between owtf
                # output and tool output
                logging.warn(line.strip())  # Show progress on the screen too!
                output += line  # Save as much output as possible before a tool crashes! :)
        except KeyboardInterrupt:
            os.killpg(proc.pid, signal.SIGINT)
            outdata, errdata = proc.communicate()
            logging.warn(outdata)
            output += outdata
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # Plugin KIA (Killed in Action)
            except OSError:
                pass  # Plugin RIP (Rested In Peace)
            cancelled = True
            output += self.error_handler.user_abort('Command', output)  # Identify as Command Level abort
        finally:
            try:
                self.finish_cmd(cmd_info, cancelled, plugin_info)
            except SQLAlchemyError as e:
                logging.error("Exception occurred while during database transaction : \n%s", str(e))
                output += str(e)
        return scrub_output(output)

    def shell_exec(self, command, **kwds):
        """This is mostly used for internal framework commands

        .note::

            # Stolen from (added shell=True tweak, necessary for easy piping straight via the command line, etc):
            # http://stackoverflow.com/questions/236737/making-a-system-call-that-returns-the-stdout-output-as-a-string/
            # 236909#236909

        :param command: Command to run
        :type command: `str`
        :param kwds: Misc. args
        :type kwds: `dict`
        :return:
        :rtype:
        """
        kwds.setdefault("stdout", subprocess.PIPE)
        kwds.setdefault("stderr", subprocess.STDOUT)
        p = subprocess.Popen(command, shell=True, **kwds)
        return p.communicate()[0]
