"""
Plugin for probing mssql
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " MsSql Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('MsSqlProbeMethods')
    # No previous output
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
