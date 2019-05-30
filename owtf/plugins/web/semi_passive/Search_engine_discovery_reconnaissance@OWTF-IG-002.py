"""
SEMI-PASSIVE Plugin for Search engine discovery/reconnaissance (OWASP-IG-002)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Metadata analysis"
ATTR = {"INTERNET_RESOURCES": True}


def run(PluginInfo):
    resource = get_resources("SemiPassiveSearchEngineDiscoveryCmd")
    Content = plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )  # No previous output
    return Content
