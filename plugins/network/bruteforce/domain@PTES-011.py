"""
Plugin for probing DNS
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " DNS Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('DomainBruteForcing'),
        PluginInfo,
        "")  # No previous output
