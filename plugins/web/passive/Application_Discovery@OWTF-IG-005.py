from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing for Application Discovery (OWASP-IG-005)
"""

DESCRIPTION = "Third party discovery resources"

def run(PluginInfo):
        # ServiceLocator.get_component("config").Show()
        # Content = ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', ServiceLocator.get_component("config").GetResources('PassiveApplicationDiscoveryCmd'), PluginInfo)
        # Content = ServiceLocator.get_component("plugin_helper").DrawResourceLinkList('Online Resources', ServiceLocator.get_component("config").GetResources('PassiveAppDiscovery'))
        resource = ServiceLocator.get_component("resource")
        Content = ServiceLocator.get_component("plugin_helper").TabbedResourceLinkList([
                                                                ['DNS', resource.GetResources('PassiveAppDiscoveryDNS')],
                                                                ['WHOIS', resource.GetResources('PassiveAppDiscoveryWHOIS')],
                                                                ['DB Lookups', resource.GetResources('PassiveAppDiscoveryDbLookup')],
                                                                ['Ping', resource.GetResources('PassiveAppDiscoveryPing')],
                                                                ['Traceroute', resource.GetResources('PassiveAppDiscoveryTraceroute')],
                                                                ['Misc', resource.GetResources('PassiveAppDiscoveryMisc')]
                                                               ])
        return Content
