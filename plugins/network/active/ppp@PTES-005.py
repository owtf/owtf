"""
Plugin for probing emc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " EMC Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('EmcProbeMethods'),
        PluginInfo, [])  # No previous output
