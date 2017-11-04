"""
Plugin for probing snmp
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " SNMP Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('BruteSnmpProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
