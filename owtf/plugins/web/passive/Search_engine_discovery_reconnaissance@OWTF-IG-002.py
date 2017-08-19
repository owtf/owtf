"""
PASSIVE Plugin for Search engine discovery/reconnaissance (OWASP-IG-002)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "General Google Hacking/Email harvesting, etc"
ATTR = {'INTERNET_RESOURCES': True}


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    resource = ServiceLocator.get_component("resource").GetResources('PassiveSearchEngineDiscoveryCmd')
    resource_online = ServiceLocator.get_component("resource").GetResources('PassiveSearchEngineDiscoveryLnk')
    Content = plugin_helper.CommandDump('Test Command', 'Output', resource, PluginInfo, [])
    Content += plugin_helper.ResourceLinkList('Online Resources', resource_online)
    return Content
