from framework.dependency_management.dependency_resolver import ServiceLocator

"""
PASSIVE Plugin for Search engine discovery/reconnaissance (OWASP-IG-002)
"""

DESCRIPTION = "General Google Hacking/Email harvesting, etc"
ATTR = {
    'INTERNET_RESOURCES': True,
}


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.CommandDump('Test Command', 'Output',
                                                                        ServiceLocator.get_component(
                                                                            "resource").GetResources(
                                                                            'PassiveSearchEngineDiscoveryCmd'),
                                                                        PluginInfo, [])
    Content += plugin_helper.ResourceLinkList('Online Resources',
                                                                              ServiceLocator.get_component(
                                                                                  "resource").GetResources(
                                                                                  'PassiveSearchEngineDiscoveryLnk'))
    return Content
