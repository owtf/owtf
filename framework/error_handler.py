#!/usr/bin/env python
"""
The error handler provides a centralised control for aborting the application
and logging errors for debugging later.
"""

import logging
import traceback
import sys
import json
import urllib2
import requests
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import ErrorHandlerInterface
from framework.lib.exceptions import FrameworkAbortException, PluginAbortException
from framework.lib.general import cprint
from framework.utils import OutputCleaner, print_version


class ErrorHandler(BaseComponent, ErrorHandlerInterface):
    Command = ''
    PaddingLength = 100
    COMPONENT_NAME = "error_handler"

    def __init__(self):
        self.register_in_service_locator()
        self.config = None
        self.Core = None
        self.db = None
        self.db_error = None
        self.Padding = "\n%s\n\n" % ("_" * self.PaddingLength)
        self.SubPadding = "\n%s\n" % ("*" * self.PaddingLength)

    def init(self):
        self.Core = self.get_component("core")
        self.db = self.get_component("db")
        self.db_error = self.get_component("db_error")
        self.config = self.get_component("config")

    def SetCommand(self, command):
        self.Command = command

    def FrameworkAbort(self, message):
        """Abort the OWTF framework.

        :warning: If it happens really early and :class:`framework.core.Core`
            has note been instanciated yet, `sys.exit()` is called with error
            code -1

        :param str message: Descriptive message about the abort.

        :return: full message explaining the abort.
        :rtype: str

        """
        message = "Aborted by Framework: %s" % message
        logging.error(message)
        if self.Core is None:
            # Core being None means that OWTF is aborting super early.
            # Therefore, force a brutal exit and throw away the message.
            sys.exit(-1)
        else:
            self.Core.finish()
        return message

    def get_option_from_user(self, options):
        return raw_input("Options: 'e'+Enter= Exit" + options + ", Enter= Next test\n")

    def UserAbort(self, level, partial_output=''):
        # Levels so far can be Command or Plugin
        message = logging.info(
            "\nThe %s was aborted by the user: Please check the report and plugin output files" % level)
        message = (
            "\nThe %s was aborted by the user: Please check the report and plugin output files" % level)
        options = ""
        if 'Command' == level:
            options = ", 'p'+Enter= Move on to next plugin"
            option = 'p'
            if 'e' == option:
                if 'Command' == level:  # Try to save partial plugin results.
                    raise FrameworkAbortException(partial_output)
            elif 'p' == option:  # Move on to next plugin.
                # Jump to next handler and pass partial output to avoid losing
                # results.
                raise PluginAbortException(partial_output)
        return message

    def LogError(self, message, trace=None):
        try:
            self.db_error.Add(message, trace)  # Log error in the DB.
        except AttributeError:
            cprint("ERROR: DB is not setup yet: cannot log errors to file!")

    def AddOWTFBug(self, message):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_trace_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        err_trace = OutputCleaner.anonymise_command("\n".join(err_trace_list))
        message = OutputCleaner.anonymise_command(message)
        output = "%sOWTF BUG: Please report the sanitised information below to help make this better.Thank you.%s" % \
            (self.Padding + self.SubPadding + print_version(self.config.Rootdir, commit_hash=True, version=True) +
             self.SubPadding)
        output += "\nMessage: %s\n" % message
        output += "\nError Trace:"
        output += "\n%s" % err_trace
        output += "\n%s" % self.Padding
        cprint(output)
        self.LogError(message, err_trace)

    def Add(self, message, bugType='owtf'):
        if bugType == 'owtf':
            return self.AddOWTFBug(message)
        else:
            output = self.Padding + message + self.SubPadding
            cprint(output)
            self.LogError(message)

    def AddGithubIssue(self, username=None, title=None, body=None, id=None):
        if id is None or username is None:
            return False
        body += "\n\nSubmitted By - @"
        body += username
        data = {'title': title, 'body': body}
        data = json.dumps(data)  # Converted to string.
        headers = {
            "Content-Type": "application/json",
            "Authorization":
                "token " + self.config.FrameworkConfigGet("GITHUB_BUG_REPORTER_TOKEN")
        }
        request = requests.post(self.config.FrameworkConfigGet("GITHUB_API_ISSUES_URL"),
                                  headers=headers,
                                  data=data)
        response = request.json()
        if request.status_code == 201:
            self.db_error.UpdateAfterGitHubReport(id, body, True, response["html_url"])

        return response
