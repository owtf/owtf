"""
Plugin for probing snmp
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " SNMP Probing "


def run(PluginInfo):
    resource = get_resources("BruteSnmpProbeMethods")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
