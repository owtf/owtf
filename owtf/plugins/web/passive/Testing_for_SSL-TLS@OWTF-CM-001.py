"""
PASSIVE Plugin for Testing_for_SSL-TLS_(OWASP-CM-001)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Third party resources"


def run(PluginInfo):
    # Vuln search box to be built in core and resued in different plugins:
    resource = ServiceLocator.get_component("resource").get_resources('PassiveSSL')
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', resource)
    return Content
