"""
Plugin for probing ftp
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " FTP Probing "


def run(PluginInfo):
    resource = get_resources("FtpProbeMethods")
    # No previous output
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
