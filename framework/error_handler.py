#!/usr/bin/env python
"""
The error handler provides a centralised control for aborting the application
and logging errors for debugging later.
"""

import logging
import traceback
import sys
import cgi
import json
import urllib2
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import ErrorHandlerInterface

from framework.lib.exceptions import FrameworkAbortException, \
                                     PluginAbortException
from framework.lib.general import cprint
from framework.utils import OutputCleaner


class ErrorHandler(BaseComponent, ErrorHandlerInterface):
    Command = ''
    PaddingLength = 100
    COMPONENT_NAME = "error_handler"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.Core = None
        self.db = None
        self.db_error = None
        self.Padding = "\n" + "_" * self.PaddingLength + "\n\n"
        self.SubPadding = "\n" + "*" * self.PaddingLength + "\n"

    def init(self):
        self.Core = self.get_component("core")
        self.db = self.get_component("db")
        self.db_error = self.get_component("db_error")

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
        return raw_input(
            "Options: 'e'+Enter= Exit" + options + ", Enter= Next test\n")

    def UserAbort(self, level, partial_output = ''):
        # Levels so far can be Command or Plugin
        message = logging.info(
            "\nThe " + level + " was aborted by the user: Please check the "
            "report and plugin output files")
        message = (
            "\nThe " + level + " was aborted by the user: Please check the "
            "report and plugin output files")
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
        # TODO: http://blog.tplus1.com/index.php/2007/09/28/the-python-logging-module-is-much-better-than-print-statements/
        exc_type, exc_value, exc_traceback = sys.exc_info()
        err_trace_list = traceback.format_exception(
            exc_type, exc_value, exc_traceback)
        err_trace = OutputCleaner.anonymise_command("\n".join(err_trace_list))
        message = OutputCleaner.anonymise_command(message)
        output = self.Padding + "OWTF BUG: Please report the sanitised " \
                 "information below to help make this better. Thank you." + \
                 self.SubPadding
        output += "\nMessage: " + message + "\n"
        output += "\nError Trace:"
        output += "\n" + err_trace
        output += "\n"+self.Padding
        cprint(output)
        self.LogError(message, err_trace)

    def Add(self, message, bugType='owtf'):
        if 'owtf' == bugType:
            return self.AddOWTFBug(message)
        else:
            output = self.Padding + message + self.SubPadding
            cprint(output)
            self.LogError(message)

    def AddGithubIssue(self, title='Bug report from OWTF', info=None, user=None):
        # TODO: Has to be ported to use db and infact add to interface.
        # Once db is implemented, better verbosity will be easy.
        error_data = self.db.ErrorData()
        for item in error_data:
            if item.startswith('Message'):
                title = item[len('Message:'):]
                break
        data = {'title':'[Auto-Generated] ' + title, 'body':''}
        # For github markdown.
        data['body'] = '#### OWTF Bug Report\n\n```' + \
                       '\n'.join(error_data) + '```\n'
        if info:
            data['body'] += "\n#### User Report\n\n"
            data['body'] += info
        if user:
            data['body'] += "\n\n#### %s" % user
        data = json.dumps(data)  # Converted to string.
        headers = {
            "Content-Type": "application/json",
            "Authorization":
                "token " + self.config.Get("GITHUB_BUG_REPORTER_TOKEN")
            }
        request = urllib2.Request(
            self.config.Get("GITHUB_API_ISSUES_URL"),
            headers=headers,
            data=data)
        response = urllib2.urlopen(request)
        decoded_resp = json.loads(response.read())
        if response.code == 201:
            cprint("Issue URL: " + decoded_resp["url"])
            return True
        else:
            return False
