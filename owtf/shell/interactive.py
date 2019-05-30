"""
owtf.shell.interactive
~~~~~~~~~~~~~~~~~~~~~~

The shell module allows running arbitrary shell commands and is critical
to the framework in order to run third party tools. The interactive shell module allows non-blocking
interaction with subprocesses running tools or remote connections (i.e. shells)
"""
import logging
import subprocess

from owtf.db.session import get_scoped_session
from owtf.shell.base import BaseShell
from owtf.shell.utils import DisconnectException, recv_some, send_all, AsyncPopen
from owtf.utils.error import user_abort

__all__ = ["InteractiveShell"]


class InteractiveShell(BaseShell):

    def __init__(self):
        BaseShell.__init__(self)  # Calling parent class to do its init part
        self.connection = None
        self.options = None
        self.session = get_scoped_session()
        self.command_time_offset = "InteractiveCommand"

    def check_conn(self, abort_message):
        """Check the connection is alive or not

        :param abort_message: Abort message to print
        :type abort_message: `str`
        :return: True if channel is open, else False
        :rtype: `bool`
        """
        if not self.connection:
            logging.warn("ERROR - Communication channel closed - %s", abort_message)
            return False
        return True

    def read(self, time=1):
        """Read data from the channel

         :param time: Time interval in seconds
         :type time: `int`
         :return: Output from the channel
         :rtype: `str`
         """
        output = ""
        if not self.check_conn("Cannot read"):
            return output
        try:
            output = recv_some(self.connection, time)
        except DisconnectException:
            logging.warn("ERROR: read - The Communication channel is down!")
            return output  # End of communication channel
        logging.info(output)  # Show progress on screen
        return output

    def format_cmd(self, command):
        """Format the command to be printed on console

        :param command: Command to run
        :type command: `str`
        :return: Formatted command string
        :rtype: `str`
        """
        if (
            "RHOST" in self.options and "RPORT" in self.options
        ):  # Interactive shell on remote connection
            return "{!s}:{!s}-{!s}".format(
                self.options["RHOST"], self.options["RPORT"], command
            )
        else:
            return "Interactive - {!s}".format(command)

    def run(self, command, plugin_info):
        """Format the command to be printed on console

         :param command: Command to run
         :type command: `str`
         :return: Formatted command string
         :rtype: `str`
         """
        output = ""
        cancelled = False
        if not self.check_conn("NOT RUNNING Interactive command: {!s}".format(command)):
            return output
        # TODO: tail to be configurable: \n for *nix, \r\n for win32
        log_cmd = self.format_cmd(command)
        cmd_info = self.start_cmd(log_cmd, log_cmd)
        try:
            logging.info("Running Interactive command: %s", command)
            send_all(self.connection, command + "\n")
            output += self.read()
            self.finish_cmd(self.session, cmd_info, cancelled, plugin_info)
        except DisconnectException:
            cancelled = True
            logging.warn("ERROR: Run - The Communication Channel is down!")
            self.finish_cmd(self.session, cmd_info, cancelled, plugin_info)
        except KeyboardInterrupt:
            cancelled = True
            self.finish_cmd(self.session, cmd_info, cancelled, plugin_info)
            output += user_abort("Command", output)  # Identify as Command Level abort
        if not cancelled:
            self.finish_cmd(self.session, cmd_info, cancelled, plugin_info)
        return output

    def run_cmd_list(self, cmd_list, plugin_info):
        """Run a list of commands

        :param cmd_list: List of commands to run
        :type cmd_list: `list`
        :param plugin_info: Plugin context information
        :type plugin_info: `dict`
        :return: Command output
        :rtype: `str`
        """
        output = ""
        for command in cmd_list:
            if command != "None":
                output += self.run(command, plugin_info)
        return output

    def open(self, options, plugin_info):
        """Open the connection channel

        :param options: User supplied args
        :type options: `dict`
        :param plugin_info: Context info for plugins
        :type plugin_info: `dict`
        :return: Plugin output
        :rtype: `str`
        """
        output = ""
        if not self.connection:
            name, command = options["ConnectVia"][0]
            self.connection = AsyncPopen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                bufsize=1,
            )
            self.options = options  # Store Options for Closing processing and if initial Commands are given
            if options["InitialCommands"]:
                output += self.run_cmd_list([options["InitialCommands"]], plugin_info)
            output += self.read()
        output += self.read()
        return output

    def close(self, plugin_info):
        """Close the communication channel

        :param plugin_info: Context information for plugin
        :type plugin_info: `dict`
        :return: None
        :rtype: None
        """
        logging.info("Close: %s", str(self.options))
        if self.options["CommandsBeforeExit"]:
            logging.info("Running commands before closing Communication Channel..")
            self.run_cmd_list(
                self.options["CommandsBeforeExit"].split(
                    self.options["CommandsBeforeExitDelim"]
                ),
                plugin_info,
            )
        logging.info("Trying to close Communication Channel..")
        self.run("exit", plugin_info)

        if self.options["ExitMethod"] == "kill":
            logging.info("Killing Communication Channel..")
            self.connection.kill()
        else:  # By default wait
            logging.info("Waiting for Communication Channel to close..")
            self.connection.wait()
        self.connection = None

    def is_closed(self):
        """Check if connection is closed

        :return: True if closed, else True
        :rtype: `bool`
        """
        return self.connection is None
