"""
owtf.wrappers.spear_phishing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome the limitations of set-automate
"""

import time

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import AbstractInterface
from owtf.lib.general import *


SCRIPT_DELAY = 2


class SpearPhishing(BaseComponent, AbstractInterface):

    COMPONENT_NAME = "spear_phishing"

    def __init__(self, set):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db_config = self.get_component("db_config")
        self.error_handler = self.get_component("error_handler")
        self.set = set

    def run(self, args, plugin_info):
        """Run all SET scripts with supplied args and plugin info

        :param args: User supplied args
        :type args: `dict`
        :param plugin_info: Context information for the plugin
        :type plugin_info: `dict`
        :return: total output
        :rtype: `str`
        """
        output = ''
        if self.init(args):
            self.set.open({
                'ConnectVia': self.get_component("resource").get_resources('OpenSET'),
                'InitialCommands': None,
                'ExitMethod': args['ISHELL_EXIT_METHOD'],
                'CommandsBeforeExit': args['ISHELL_COMMANDS_BEFORE_EXIT'],
                'CommandsBeforeExitDelim': args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM']},
                plugin_info)
            if args['PHISHING_CUSTOM_EXE_PAYLOAD_DIR']:  # Prepend directory to payload
                args['PHISHING_CUSTOM_EXE_PAYLOAD'] = "%s/%s" % (args['PHISHING_CUSTOM_EXE_PAYLOAD_DIR'],
                                                                 args['PHISHING_CUSTOM_EXE_PAYLOAD'])
            for script in self.get_set_scripts(args):
                cprint("Running SET script: %s" % script)
                output += self.set.run_script(script, args, plugin_info, debug=False)
                cprint("Sleeping %s seconds.." % str(SCRIPT_DELAY))
                time.sleep(int(SCRIPT_DELAY))
            self.set.close(plugin_info)
        return output

    def get_set_scripts(self, args):
        """Get the list of all available set scripts

        :param args: User supplied args
        :type args: `dict`
        :return: List of script names
        :rtype: `list`
        """
        return ["%s/start_phishing.set" % args['PHISHING_SCRIPT_DIR'],
                "%s/payload_%s.set" % (args['PHISHING_SCRIPT_DIR'], args['PHISHING_PAYLOAD']),
                "%s/send_email_smtp.set" % args['PHISHING_SCRIPT_DIR']
                ]

    def init_paths(self, args):
        """Initiatize paths for the scripts

        :param args: User supplied args
        :type args: `dict`
        :return: True if scripts found at the paths
        :rtype:
        """
        mandatory_paths = self.config.get_as_list(['_PDF_TEMPLATE', '_WORD_TEMPLATE', '_EMAIL_TARGET'])
        mandatory_paths.append(self.db_config.Get('TOOL_SET_DIR'))
        if not paths_exist(mandatory_paths) or not paths_exist(self.get_set_scripts(args)):
            self.error_handler.abort_framework("USER ERROR: Some mandatory paths were not found your filesystem",
                                              'user')
            return False
        return True

    def init(self, args):
        """Run the init paths function and check output

        :param args: User supplied args
        :type args: `dict`
        :return: True if function returns successfully, else False
        :rtype: `bool`
        """
        if not self.init_paths(args):
            return False
        return True
