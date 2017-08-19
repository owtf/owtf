"""
PASSIVE Plugin for Testing_for_SSI_Injection@OWASP-DV-009
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Searching for pages that are susceptible to SSI-Injection"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('PassiveSSIDiscoveryLnk')
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', resource)
    return Content
