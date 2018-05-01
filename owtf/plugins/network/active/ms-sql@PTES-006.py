"""
Plugin for probing mssql
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " MsSql Probing "


def run(PluginInfo):
    resource = get_resources("MsSqlProbeMethods")
    # No previous output
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
