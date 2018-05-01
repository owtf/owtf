"""
Plugin for probing HTTP Rpc
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " HTTP Rpc Probing "


def run(PluginInfo):
    resource = get_resources("HttpRpcProbeMethods")
    # No previous output
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
