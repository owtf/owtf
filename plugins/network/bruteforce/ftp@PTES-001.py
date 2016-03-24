"""
Plugin for probing ftp
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " FTP Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('BruteFtpProbeMethods'),
        PluginInfo, [])  # No previous output
