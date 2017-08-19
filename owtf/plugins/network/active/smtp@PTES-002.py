"""
Plugin for probing smtp
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " SMTP Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('SmtpProbeMethods')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
