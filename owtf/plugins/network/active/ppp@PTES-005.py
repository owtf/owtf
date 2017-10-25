"""
Plugin for probing emc
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " EMC Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('EmcProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
