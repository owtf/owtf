"""
Plugin for probing MsRpc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " MsRpc Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('MsRpcProbeMethods'),
        PluginInfo, [])  # No previous output
