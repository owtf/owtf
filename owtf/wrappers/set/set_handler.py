"""
owtf.wrappers.set.set_handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome the limitations of set-automate
"""

import time

from owtf.lib.general import *
from owtf.shell import pexpect_shell


class SETHandler(pexpect_shell.PExpectShell):

    def __init__(self):
        pexpect_shell.PExpectShell.__init__(self)  # Calling parent class to do its init part
        self.command_time_offset = 'SETCommand'

    def run_script(self, script_path, args, plugin_info, debug=False):
        """Runs the set script with context information and user args

        :param script_path: The set script to run
        :type script_path: `str`
        :param args: User supplied args
        :type args: `dict`
        :param plugin_info: Context info for the plugin
        :type plugin_info: `dict`
        :param debug: Use debug mode
        :type debug: `bool`
        :return: Output of the script
        :rtype: `str`
        """
        # TODO: Replacements
        output = ""
        for step in multi_replace(open(script_path).read(), args).split("\n"):
            if not step.strip():
                cprint("WARNING: Sending Blank!")  # Necessary sometimes, but warn
            if debug:
                print("Step: %s" % str(step))
            else:
                output += self.run(step, plugin_info)
                if step == 'exit':
                    self.kill()
                cprint("Waiting %s  seconds for SET to process step.. - %s" % (args['ISHELL_DELAY_BETWEEN_COMMANDS'],
                                                                               step))
                time.sleep(int(args['ISHELL_DELAY_BETWEEN_COMMANDS']))
                self.expect('set.*>|Password for open-relay', TimeOut=120)
        return output
