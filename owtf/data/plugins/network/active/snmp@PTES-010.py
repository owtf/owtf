"""
Plugin for probing snmp
"""
from owtf.managers.resource import get_resources
from owtf.plugin.plugin_helper import plugin_helper


DESCRIPTION = " SNMP Probing "


def run(PluginInfo):
    resource = get_resources('SnmpProbeMethods')
    return plugin_helper.CommandDump('Test Command', 'Output', resource, PluginInfo, [])
