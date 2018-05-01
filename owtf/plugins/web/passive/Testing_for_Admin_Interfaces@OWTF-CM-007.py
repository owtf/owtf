"""
PASSIVE Plugin for Testing for Admin Interfaces (OWASP-CM-007)
https://www.owasp.org/index.php/Testing_for_Admin_Interfaces_%28OWASP-CM-007%29
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Google Hacking for Admin interfaces"


def run(PluginInfo):
    resource = get_resources("PassiveAdminInterfaceLnk")
    Content = plugin_helper.resource_linklist("Online Resources", resource)
    return Content
