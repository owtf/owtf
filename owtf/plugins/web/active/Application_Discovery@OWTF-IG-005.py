"""
ACTIVE Plugin for Testing for Application Discovery (OWASP-IG-005)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active probing for app discovery"


def run(PluginInfo):
    resource = get_resources("ActiveDiscovery")
    # No previous output
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
