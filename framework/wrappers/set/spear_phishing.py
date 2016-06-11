#!/usr/bin/env python
'''
Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome the limitations of set-automate
'''

import time

from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import AbstractInterface
from framework.lib.general import *


SCRIPT_DELAY = 2


class SpearPhishing(BaseComponent, AbstractInterface):

    COMPONENT_NAME = "spear_phishing"

    def __init__(self, set):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.error_handler = self.get_component("error_handler")
        self.set = set

    def Run(self, Args, PluginInfo):
        Output = ''
        if self.Init(Args):
            self.set.Open({
                'ConnectVia': self.config.GetResources('OpenSET'),
                'InitialCommands': None,
                'ExitMethod': Args['ISHELL_EXIT_METHOD'],
                'CommandsBeforeExit': Args['ISHELL_COMMANDS_BEFORE_EXIT'],
                'CommandsBeforeExitDelim': Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM']},
                PluginInfo)
            if Args['PHISHING_CUSTOM_EXE_PAYLOAD_DIR']:  # Prepend directory to payload
                Args['PHISHING_CUSTOM_EXE_PAYLOAD'] = "%s/%s" % (Args['PHISHING_CUSTOM_EXE_PAYLOAD_DIR'],
                                                                 Args['PHISHING_CUSTOM_EXE_PAYLOAD'])
            for Script in self.GetSETScripts(Args):
                cprint("Running SET script: %s" % Script)
                Output += self.set.RunScript(Script, Args, Debug=False)
                cprint("Sleeping %s seconds.." % str(SCRIPT_DELAY))
                time.sleep(int(SCRIPT_DELAY))
            self.set.Close(PluginInfo)
        return Output

    def GetSETScripts(self, Args):
        return ["%s/start_phishing.set" % Args['PHISHING_SCRIPT_DIR'],
                "%s/payload_%s.set" % (Args['PHISHING_SCRIPT_DIR'], Args['PHISHING_PAYLOAD']),
                "%s/send_email_smtp.set" % Args['PHISHING_SCRIPT_DIR']
                ]

    def InitPaths(self, Args):
        MandatoryPaths = self.config.GetAsList(['TOOL_SET_DIR', '_PDF_TEMPLATE', '_WORD_TEMPLATE', '_EMAIL_TARGET'])
        if not PathsExist(MandatoryPaths) or not PathsExist(self.GetSETScripts(Args)):
            self.error_handler.FrameworkAbort("USER ERROR: Some mandatory paths were not found your filesystem",
                                              'user')
            return False
        return True

    def Init(self, Args):
        if not self.InitPaths(Args):
            return False
        return True
