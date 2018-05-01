"""
PASSIVE Plugin for HTTP Methods Testing
"""
import logging

from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Third party resources"


def run(PluginInfo):
    # Vuln search box to be built in core and resued in different plugins:
    resource = get_resources("PassiveMethods")
    Content = plugin_helper.resource_linklist("Online Resources", resource)
    logging.info("Passive links generated for target")
    return Content
