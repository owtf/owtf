"""
Plugin for probing DNS
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " DNS Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").get_resources('DomainBruteForcing'),
        PluginInfo,
        "")  # No previous output
