"""
Plugin for probing MsRpc
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " MsRpc Probing "


def run(PluginInfo):
    resource = get_resources("MsRpcProbeMethods")
    # No previous output
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
