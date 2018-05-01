"""
Plugin for probing SMB
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " SMB Probing "


def run(PluginInfo):
    resource = get_resources("BruteSmbProbeMethods")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
