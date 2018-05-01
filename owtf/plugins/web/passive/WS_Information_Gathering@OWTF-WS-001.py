"""
PASSIVE Plugin for Testing: WS Information Gathering (OWASP-WS-001)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Google Hacking/Third party sites for Web Services"


def run(PluginInfo):
    resource = get_resources("WSPassiveSearchEngineDiscoveryLnk")
    return plugin_helper.resource_linklist("Online Resources", resource)
