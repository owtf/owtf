"""
Plugin for probing snmp
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " SNMP Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('BruteSnmpProbeMethods'),
        PluginInfo, [])  # No previous output
