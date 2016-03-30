"""
PASSIVE Plugin for Testing_for_SSL-TLS_(OWASP-CM-001)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Third party resources"


def run(PluginInfo):
    # Vuln search box to be built in core and resued in different plugins:
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList(
        'Online Resources',
        ServiceLocator.get_component("resource").GetResources('PassiveSSL'))
    return Content
