#!/usr/bin/env python
"""
The health-check module verifies the integrity of the configuration, mainly
checking that tool paths exist.
"""

import os
from framework.dependency_management.dependency_resolver import BaseComponent
import logging



class HealthCheck(BaseComponent):

    """Verifies the integrity of the configuration.

    Mainly checks that tool paths exist and counts how many are missing.
    If tools are missing, display the total number of missing one and their
    names.

    """

    def __init__(self):
        self.config = self.get_component("config")
        self.error_handler = self.get_component("error_handler")
        self.db_config = self.get_component("db_config")
        self.run()

    def run(self):
        count = self.count_not_installed_tools()
        self.show_help(count)

    def count_not_installed_tools(self):
        """Count the number of missing tools by checking their paths."""
        count = 0
        tool_settings = self.db_config.GetAllTools()
        for tool_setting in tool_settings:
            if self.is_tool(tool_setting['key']) and not self.is_installed(tool_setting['value']):
                logging.error("WARNING: Tool path not found for: " + str(tool_setting['value']))
                count += 1
        return count

    @staticmethod
    def is_tool(setting):
        return setting.startswith('TOOL_')

    @staticmethod
    def is_installed(value):
        return os.path.exists(value)

    def show_help(self, count):
        if count > 0:
            self.print_warning(count)
        else:
            self.print_success()

    def print_warning(self, count):
        logging.info(
            "WARNING!!!: " +
            str(count) +
            " tools could not be found. Some suggestions:")
        logging.info(
            " - You can define your tool paths from the interface as well ")
        if ('n' == raw_input("Continue anyway? [Y/n]")):
            self.error_handler.FrameworkAbort("Aborted by user")

    @staticmethod
    def print_success():
        logging.info(
            "SUCCESS: Integrity Check successful -> All tools were found")
