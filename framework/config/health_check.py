#!/usr/bin/env python
"""

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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The health-check module verifies the integrity of the configuration, mainly
checking that tool paths exist.

"""

import os

from framework.lib.general import cprint


class HealthCheck(object):

    """Verifies the integrity of the configuration.

    Mainly checks that tool paths exist and counts how many are missing.
    If tools are missing, display the total number of missing one and their
    names.

    """

    def __init__(self, core):
        self.core = core

    def run(self):
        count = self.count_not_installed_tools()
        self.show_help(count)

    def count_not_installed_tools(self):
        """Count the number of missing tools by checking their paths."""
        count = 0
        for key, value in self.core.Config.GetConfig():
            setting = self.core.Config.StripKey(key)
            if self.is_tool(setting) and not self.is_installed(value):
                cprint("WARNING: Tool path not found for: " + str(value))
                count += 1
        return count

    @classmethod
    def is_tool(cls, setting):
        return setting.startswith('TOOL_')

    @classmethod
    def is_installed(cls, value):
        return os.path.exists(value)

    def show_help(self, count):
        if count > 0:
            self.print_warning(count)
        else:
            self.print_success()

    def print_warning(self, count):
        cprint("")
        cprint(
            "WARNING!!!: " +
            str(count) +
            " tools could not be found. Some suggestions:")
        cprint(
            " - Define where your tools are here: " +
            str(self.core.Config.Profiles['g']))
        if (self.core.Config.Get('INTERACTIVE') and
                'n' == raw_input("Continue anyway? [Y/n]")):
            self.core.Error.FrameworkAbort("Aborted by user")

    @classmethod
    def print_success(cls):
        return cprint(
            "SUCCESS: Integrity Check successful -> All tools were found")
