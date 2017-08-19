"""
Plugin for probing HTTP Rpc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " HTTP Rpc Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('HttpRpcProbeMethods')
    # No previous output
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
