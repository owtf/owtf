#!/usr/bin/env python
'''
Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome the limitations of set-automate
'''

import time

from framework.lib.general import *
from framework.shell import pexpect_shell
from framework.wrappers.set import spear_phishing


class SETHandler(pexpect_shell.PExpectShell):
    def __init__(self):
        pexpect_shell.PExpectShell.__init__(self)  # Calling parent class to do its init part
        self.CommandTimeOffset = 'SETCommand'
        self.SpearPhishing = spear_phishing.SpearPhishing(self)

    def RunScript(self, ScriptPath, Args, Debug=False):
        # TODO: Replacements
        Output = ""
        for Step in MultipleReplace(open(ScriptPath).read(), Args).split("\n"):
            if not Step.strip():
                cprint("WARNING: Sending Blank!")  # Necessary sometimes, but warn
            if Debug:
                print("Step: %s" % str(Step))
            else:
                Output += self.Run(Step)
                if Step == 'exit':
                    self.Kill()
                cprint("Waiting %s  seconds for SET to process step.. - %s" % (Args['ISHELL_DELAY_BETWEEN_COMMANDS'],
                                                                               Step))
                time.sleep(int(Args['ISHELL_DELAY_BETWEEN_COMMANDS']))
                self.Expect('set.*>|Password for open-relay', TimeOut=120)
        return Output
