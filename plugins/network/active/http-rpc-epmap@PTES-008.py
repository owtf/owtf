"""
Plugin for probing HTTP Rpc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " HTTP Rpc Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('HttpRpcProbeMethods'),
        PluginInfo, [])  # No previous output
