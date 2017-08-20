"""
PASSIVE Plugin for Testing for Application Discovery (OWASP-IG-005)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Third party discovery resources"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource")
    Content = ServiceLocator.get_component("plugin_helper").TabbedResourceLinkList([
        ['DNS', resource.get_resources('PassiveAppDiscoveryDNS')],
        ['WHOIS', resource.get_resources('PassiveAppDiscoveryWHOIS')],
        ['DB Lookups', resource.get_resources('PassiveAppDiscoveryDbLookup')],
        ['Ping', resource.get_resources('PassiveAppDiscoveryPing')],
        ['Traceroute', resource.get_resources('PassiveAppDiscoveryTraceroute')],
        ['Misc', resource.get_resources('PassiveAppDiscoveryMisc')]
    ])
    return Content
