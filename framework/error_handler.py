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
and logging errors for debugging later

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

        def SetCommand(self, Command):
                self.Command = Command

        def FrameworkAbort(self, Message, Report = True):
                Message = "Aborted by Framework: "+Message
                cprint(Message)
                self.Core.Finish(Message, Report)
                return Message

        def get_option_from_user(self, Options):
            return raw_input("Options: 'e'+Enter= Exit" + Options + ", Enter= Next test\n")

        def UserAbort(self, Level, PartialOutput = ''): # Levels so far can be Command or Plugin
                Message = log("\nThe "+Level+" was aborted by the user: Please check the report and plugin output files")
                Message = ("\nThe "+Level+" was aborted by the user: Please check the report and plugin output files")
                Options = ""
                if 'Command' == Level:
                        Options = ", 'p'+Enter= Move on to next plugin"
                        Option = 'p'#raw_input("Options: 'e'+Enter= Exit"+Options+", Enter= Next test\n")
                        if 'e' == Option:
                                if 'Command' == Level: # Try to save partial plugin results
                                        raise FrameworkAbortException(PartialOutput)
                                        self.Core.Finish("Aborted by user") # Interrupted
                        elif 'p' == Option: # Move on to next plugin
                                raise PluginAbortException(PartialOutput) # Jump to next handler and pass partial output to avoid losing results
                return Message

        def LogError(self, Message, Trace=None):
                try:
                        self.Core.DB.Error.Add(Message, Trace) # Log error in the DB
                except AttributeError:
                        cprint("ERROR: DB is not setup yet: cannot log errors to file!")

        def AddOWTFBug(self, Message):
                exc_type, exc_value, exc_traceback = sys.exc_info()
                ErrorTraceList = traceback.format_exception(exc_type, exc_value, exc_traceback)
                ErrorTrace = self.Core.AnonymiseCommand("\n".join(ErrorTraceList))
                #traceback.print_exc()
                #print repr(traceback.format_stack())
                #print repr(traceback.extract_stack())
                Message = self.Core.AnonymiseCommand(Message)
                Output = self.Padding+"OWTF BUG: Please report the sanitised information below to help make this better. Thank you."+self.SubPadding
                Output += "\nMessage: "+Message+"\n"
                Output += "\nError Trace:"
                Output += "\n"+ErrorTrace
                Output += "\n"+self.Padding
                cprint(Output)
                self.LogError(Message, ErrorTrace)
                #TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/

        def Add(self, Message, BugType = 'owtf'):
                if 'owtf' == BugType:
                        return self.AddOWTFBug(Message)
                else:
                        Output = self.Padding+Message+self.SubPadding
                        cprint(Output)
                        self.LogError(Message)

        def AddGithubIssue(self, Title='Bug report from OWTF', Info=None, User=None):
                # TODO: Has to be ported to use db and infact add to interface
                # Once db is implemented, better verbosity will be easy
                error_data = self.Core.DB.ErrorData()
                for item in error_data:
                    if item.startswith('Message'):
                        Title = item[len('Message:'):]
                        break
                data = {'title':'[Auto-Generated] ' + Title, 'body':''}
                data['body'] = '#### OWTF Bug Report\n\n```' + '\n'.join(error_data) + '```\n' # For github markdown
                if Info:
                    data['body'] += "\n#### User Report\n\n"
                    data['body'] += Info
                if User:
                    data['body'] += "\n\n#### %s" %(User)
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
