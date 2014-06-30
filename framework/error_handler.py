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

The error handler provides a centralised control for aborting the application
and logging errors for debugging later.

"""

import logging
import traceback
import sys
import cgi
import json
import urllib2

from framework.lib.exceptions import FrameworkAbortException, \
                                     PluginAbortException
from framework.lib.general import cprint, log


class ErrorHandler(object):
    Command = ''
    PaddingLength = 100

    def __init__(self, Core):
        self.Core = Core
        self.Padding = "\n" + "_" * self.PaddingLength + "\n\n"
        self.SubPadding = "\n" + "*" * self.PaddingLength + "\n"

    def SetCommand(self, command):
        self.Command = command

    def FrameworkAbort(self, message, report=True):
        message = "Aborted by Framework: " + message
        cprint(message)
        self.Core.Finish(message, report)
        return message

    def get_option_from_user(self, options):
        return raw_input("Options: 'e'+Enter= Exit" + options + ", Enter= Next test\n")

    def UserAbort(self, level, partial_output = ''): # Levels so far can be Command or Plugin
        message = log("\nThe " + level + " was aborted by the user: Please check the report and plugin output files")
        message = ("\nThe " + level + " was aborted by the user: Please check the report and plugin output files")
        options = ""
        if 'Command' == level:
            options = ", 'p'+Enter= Move on to next plugin"
            option = 'p'
            if 'e' == option:
                if 'Command' == level: # Try to save partial plugin results
                    raise FrameworkAbortException(partial_output)
                    self.Core.Finish("Aborted by user") # Interrupted
            elif 'p' == option: # Move on to next plugin
                raise PluginAbortException(partial_output) # Jump to next handler and pass partial output to avoid losing results
        return message

    def LogError(self, message, trace=None):
        try:
            self.Core.DB.Error.Add(message, trace) # Log error in the DB
        except AttributeError:
            cprint("ERROR: DB is not setup yet: cannot log errors to file!")

    def AddOWTFBug(self, message):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_trace_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        err_trace = self.Core.AnonymiseCommand("\n".join(err_trace_list))
        message = self.Core.AnonymiseCommand(message)
        output = self.Padding+"OWTF BUG: Please report the sanitised information below to help make this better. Thank you."+self.SubPadding
        output += "\nMessage: " + message + "\n"
        output += "\nError Trace:"
        output += "\n" + err_trace
        output += "\n"+self.Padding
        cprint(output)
        self.LogError(message, err_trace)
        #TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/

    def Add(self, message, bugType='owtf'):
        if 'owtf' == bugType:
            return self.AddOWTFBug(message)
        else:
            output = self.Padding + message + self.SubPadding
            cprint(output)
            self.LogError(message)

    def AddGithubIssue(self, title='Bug report from OWTF', info=None, user=None):
        # TODO: Has to be ported to use db and infact add to interface
        # Once db is implemented, better verbosity will be easy
        error_data = self.Core.DB.ErrorData()
        for item in error_data:
            if item.startswith('Message'):
                title = item[len('Message:'):]
                break
        data = {'title':'[Auto-Generated] ' + title, 'body':''}
        data['body'] = '#### OWTF Bug Report\n\n```' + '\n'.join(error_data) + '```\n' # For github markdown
        if info:
            data['body'] += "\n#### User Report\n\n"
            data['body'] += info
        if user:
            data['body'] += "\n\n#### %s" % user
        data = json.dumps(data) # Converted to string
        headers = {"Content-Type": "application/json","Authorization": "token " + self.Core.Config.Get("GITHUB_BUG_REPORTER_TOKEN")}
        request = urllib2.Request(self.Core.Config.Get("GITHUB_API_ISSUES_URL"), headers=headers, data=data)
        response = urllib2.urlopen(request)
        decoded_resp = json.loads(response.read())
        if response.code == 201:
            cprint("Issue URL: " + decoded_resp["url"])
            return True
        else:
            return False
