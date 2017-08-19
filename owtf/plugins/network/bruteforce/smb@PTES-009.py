"""
Plugin for probing SMB
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " SMB Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('BruteSmbProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
