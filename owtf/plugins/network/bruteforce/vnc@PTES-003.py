"""
Plugin for probing vnc
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " VNC Probing "


def run(PluginInfo):
    resource = get_resources("BruteVncProbeMethods")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
