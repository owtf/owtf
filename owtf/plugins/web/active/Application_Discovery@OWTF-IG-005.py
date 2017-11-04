"""
ACTIVE Plugin for Testing for Application Discovery (OWASP-IG-005)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Active probing for app discovery"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ActiveDiscovery')
    # No previous output
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                     resource, PluginInfo, [])
