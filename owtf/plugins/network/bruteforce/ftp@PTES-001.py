"""
Plugin for probing ftp
"""

from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " FTP Probing "


def run(PluginInfo):
    resource = get_resources("BruteFtpProbeMethods")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
