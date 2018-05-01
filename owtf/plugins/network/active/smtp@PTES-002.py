"""
Plugin for probing smtp
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " SMTP Probing "


def run(PluginInfo):
    resource = get_resources("SmtpProbeMethods")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
