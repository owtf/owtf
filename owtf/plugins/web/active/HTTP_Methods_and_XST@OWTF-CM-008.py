"""
ACTIVE Plugin for Testing for HTTP Methods and XST (OWASP-CM-008)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Active probing for HTTP methods"


def run(PluginInfo):
    target = ServiceLocator.get_component("target")
    URL = target.Get('top_url')
    # TODO: PUT not working right yet
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.TransactionTableForURL(True, URL, Method='TRACE')
    resource = ServiceLocator.get_component("resource")
    Content += plugin_helper.CommandDump('Test Command', 'Output', resource.get_resources('ActiveHTTPMethods'),
                                         PluginInfo, Content)
    return Content
