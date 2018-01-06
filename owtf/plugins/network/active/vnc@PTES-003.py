"""
Plugin for probing vnc
"""
from owtf.managers.resource import get_resources
from owtf.plugin.plugin_helper import plugin_helper


DESCRIPTION = " VNC Probing "


def run(PluginInfo):
    resource = get_resources('VncProbeMethods')
    return plugin_helper.CommandDump('Test Command', 'Output', resource, PluginInfo, [])
