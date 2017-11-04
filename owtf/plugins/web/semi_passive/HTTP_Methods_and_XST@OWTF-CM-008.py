"""
SEMI-PASSIVE Plugin for Testing for HTTP Methods and XST (OWASP-CM-008)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Normal request for HTTP methods analysis"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    target = ServiceLocator.get_component("target")
    resource = ServiceLocator.get_component("resource").get_resources('SemiPassiveHTTPMethods')
    Content = plugin_helper.TransactionTableForURLList(True, target.get_as_list(['target_url', 'top_url']), 'OPTIONS')
    # No previous output
    Content += plugin_helper.CommandDump('Test Command', 'Output', resource, PluginInfo, [])
    return Content
