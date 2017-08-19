"""
PASSIVE Plugin for Testing: WS Information Gathering (OWASP-WS-001)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking/Third party sites for Web Services"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('WSPassiveSearchEngineDiscoveryLnk')
    return ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', resource)
