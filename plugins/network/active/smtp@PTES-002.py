"""
Plugin for probing smtp
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = " SMTP Probing "


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('SmtpProbeMethods'),
        PluginInfo, [])  # No previous output
