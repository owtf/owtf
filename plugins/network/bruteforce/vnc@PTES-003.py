"""
Plugin for probing vnc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " VNC Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('BruteVncProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
