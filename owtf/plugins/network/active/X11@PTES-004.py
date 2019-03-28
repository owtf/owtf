"""
Plugin for probing x11
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " x11 Probing "


def run(PluginInfo):
    resource = get_resources("X11ProbeMethods")
    return plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )  # No previous output
