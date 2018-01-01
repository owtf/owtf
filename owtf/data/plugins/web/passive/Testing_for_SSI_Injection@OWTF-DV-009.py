"""
PASSIVE Plugin for Testing_for_SSI_Injection@OWASP-DV-009
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Searching for pages that are susceptible to SSI-Injection"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveSSIDiscoveryLnk')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
