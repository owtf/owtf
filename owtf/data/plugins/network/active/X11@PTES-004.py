"""
Plugin for probing x11
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " x11 Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('X11ProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                     resource, PluginInfo, [])  # No previous output
