"""
Plugin for probing smtp
"""
from owtf.managers.resource import get_resources
from owtf.plugin.plugin_helper import plugin_helper


DESCRIPTION = " SMTP Probing "


def run(PluginInfo):
    resource = get_resources('SmtpProbeMethods')
    return plugin_helper.CommandDump('Test Command', 'Output', resource, PluginInfo, [])
