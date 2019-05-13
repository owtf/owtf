"""
owtf.shell.pexpect_sh
~~~~~~~~~~~~~~~~~~~~~

"""
import logging
import sys

import pexpect

from owtf.db.session import get_scoped_session
from owtf.shell.base import BaseShell
from owtf.utils.error import user_abort

__all__ = ["PExpectShell"]


class PExpectShell(BaseShell):

    def __init__(self):
        BaseShell.__init__(self)  # Calling parent class to do its init part
        self.connection = None
        self.options = None
        self.session = get_scoped_session()
        self.command_time_offset = "PExpectCommand"

    def check_conn(self, abort_message):
        """Check the connection is alive or notp

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
            output = self.connection.after
            if output is None:
                output = ""
            logging.info(output)  # Show progress on screen
        except pexpect.EOF:
            logging.warn("ERROR: read - The Communication channel is down!")
            return output  # End of communication channel
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
        """Run the interactive command

        :param command: Command to run
        :type command: `str`
        :param plugin_info: Context info for the plugin
        :type plugin_info: `dict`
        :return: Plugin output
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
            self.connection.sendline(command)
            self.finish_cmd(self.session, cmd_info, cancelled, plugin_info)
        except pexpect.EOF:
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

    def expect(self, pattern, timeout=-1):
        """Check that channel is open by sending dummy data

        :param pattern: Pattern to check
        :type pattern: `str`
        :param timeout: Timeouts when data send and receive
        :type timeout: `int`
        :return: True if connection is alive, else False
        :rtype: `bool`
        """
        if self.connection is None:
            return False
        try:
            self.connection.expect(pattern, timeout)
        except pexpect.EOF:
            logging.warn("ERROR: Expect - The Communication Channel is down!")
        except pexpect.TIMEOUT:
            logging.warn(
                "ERROR: Expect timeout threshold exceeded for pattern %s!", pattern
            )
            logging.info("Before:")
            logging.info(self.connection.after)
            logging.info("After:")
            logging.info(self.connection.after)
        return True

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
        self.options = options  # Store options for Closing processing
        output = ""
        if not self.connection:
            cmd_list = ["bash"]
            if "ConnectVia" in options:
                name, command = options["ConnectVia"][0]
                cmd_list += command.split(";")
            cmd_count = 1
            for cmd in cmd_list:
                if cmd_count == 1:
                    try:
                        self.connection = pexpect.spawn(cmd)
                        self.connection.logfile = sys.stdout  # Ensure screen feedback
                    except ValueError as e:
                        logging.info(e.message)
                else:
                    self.run(cmd, plugin_info)
                cmd_count += 1
            if "InitialCommands" in options and options["InitialCommands"]:
                output += self.run_cmd_list(options["InitialCommands"], plugin_info)
        return output

    def kill(self):
        """Kill the communication channel

        :return: None
        :rtype: None
        """
        logging.info("Killing Communication Channel..")
        if self.connection is not None:
            self.connection.kill(0)
            self.connection = None

    def wait(self):
        """Wait for the communication channel to close

        :return: None
        :rtype: None
        """
        logging.info("Waiting for Communication Channel to close..")
        self.connection.wait()
        self.connection = None

    def close(self, plugin_info):
        """Close the communication channel

        :param plugin_info: Context information for plugin
        :type plugin_info: `dict`
        :return: None
        :rtype: None
        """
        if self.connection is None:
            logging.info("Close: Connection already closed")
            return False
        if "CommandsBeforeExit" in self.options and self.options["CommandsBeforeExit"]:
            logging.info("Running commands before closing Communication Channel..")
            self.run_cmd_list(
                self.options["CommandsBeforeExit"].split(
                    self.options["CommandsBeforeExitDelim"]
                ),
                plugin_info,
            )
        logging.info("Trying to close Communication Channel..")
        self.run("exit", plugin_info)

        if "ExitMethod" in self.options and self.options["ExitMethod"] == "kill":
            self.kill()
        else:  # By default wait
            self.wait()

    def is_closed(self):
        """Check if connection is closed

        :return: True if closed, else True
        :rtype: `bool`
        """
        return self.connection is None
