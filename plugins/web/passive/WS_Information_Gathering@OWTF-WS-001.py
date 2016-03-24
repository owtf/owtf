"""
PASSIVE Plugin for Testing: WS Information Gathering (OWASP-WS-001)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Google Hacking/Third party sites for Web Services"


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").ResourceLinkList(
        'Online Resources',
        ServiceLocator.get_component("resource").GetResources('WSPassiveSearchEngineDiscoveryLnk'))
