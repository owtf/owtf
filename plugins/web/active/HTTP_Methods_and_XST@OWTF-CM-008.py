"""
ACTIVE Plugin for Testing for HTTP Methods and XST (OWASP-CM-008)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.lib.general import get_random_str


DESCRIPTION = "Active probing for HTTP methods"


def run(PluginInfo):
    target = ServiceLocator.get_component("target")
    URL = target.Get('top_url')
    # TODO: PUT not working right yet
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.TransactionTableForURL(True, URL, Method='TRACE')
    resource = ServiceLocator.get_component("resource")
    Content += plugin_helper.CommandDump('Test Command', 'Output', resource.GetResources('ActiveHTTPMethods'), 
        PluginInfo, Content)
    return Content
