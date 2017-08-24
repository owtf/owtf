"""
PASSIVE Plugin for Testing for SQL Injection (OWASP-DV-005)
https://www.owasp.org/index.php/Testing_for_SQL_Injection_%28OWASP-DV-005%29
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking for SQLi"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveSQLInjectionLnk')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
