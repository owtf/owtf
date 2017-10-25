"""
SEMI-PASSIVE Plugin for Search engine discovery/reconnaissance (OWASP-IG-002)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Metadata analysis"
ATTR = {'INTERNET_RESOURCES': True}


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('SemiPassiveSearchEngineDiscoveryCmd')
    Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                        resource, PluginInfo, [])  # No previous output
    return Content
