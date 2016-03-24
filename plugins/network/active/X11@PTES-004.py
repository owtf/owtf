"""
Plugin for probing x11
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " x11 Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('X11ProbeMethods'),
        PluginInfo, [])  # No previous output
