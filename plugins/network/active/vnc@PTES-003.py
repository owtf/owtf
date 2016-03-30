"""
Plugin for probing vnc
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " VNC Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('VncProbeMethods'),
        PluginInfo, [])  # No previous output
