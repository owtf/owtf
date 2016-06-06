"""
PASSIVE Plugin for Testing for Application Discovery (OWASP-IG-005)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Third party discovery resources"


def run(PluginInfo):
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
