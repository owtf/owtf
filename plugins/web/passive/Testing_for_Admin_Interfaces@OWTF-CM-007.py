"""
PASSIVE Plugin for Testing for Admin Interfaces (OWASP-CM-007)
https://www.owasp.org/index.php/Testing_for_Admin_Interfaces_%28OWASP-CM-007%29
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Google Hacking for Admin interfaces"


def run(PluginInfo):
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList(
        'Online Resources',
        ServiceLocator.get_component("resource").GetResources('PassiveAdminInterfaceLnk'))
    return Content
