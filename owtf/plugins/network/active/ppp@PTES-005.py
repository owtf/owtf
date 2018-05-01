"""
Plugin for probing emc
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " EMC Probing "


def run(PluginInfo):
    resource = get_resources("EmcProbeMethods")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
