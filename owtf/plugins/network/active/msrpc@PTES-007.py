"""
Plugin for probing MsRpc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " MsRpc Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('MsRpcProbeMethods')
    # No previous output
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
