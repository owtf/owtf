"""
ACTIVE Plugin for Testing for SSL-TLS (OWASP-CM-001)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Active probing for SSL configuration"


def run(PluginInfo):
    Content = ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('ActiveSSLCmds'),
        PluginInfo, [])  # No previous output
    return Content
