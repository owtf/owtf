"""
Plugin for probing mssql
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " MsSql Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('MsSqlProbeMethods'),
        PluginInfo, [])  # No previous output
