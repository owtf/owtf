"""
Plugin for probing vnc
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " VNC Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('BruteVncProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
