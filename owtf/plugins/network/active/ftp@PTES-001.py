"""
Plugin for probing ftp
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = " FTP Probing "


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('FtpProbeMethods')
    # No previous output
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource, PluginInfo, [])
