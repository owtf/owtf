"""
PASSIVE Plugin for Testing_for_SSI_Injection@OWASP-DV-009
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Searching for pages that are susceptible to SSI-Injection"


def run(PluginInfo):
    resource = get_resources("PassiveSSIDiscoveryLnk")
    Content = plugin_helper.resource_linklist("Online Resources", resource)
    return Content
