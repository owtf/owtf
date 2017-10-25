"""
PASSIVE Plugin for Testing for Error Code (OWASP-IG-006)
https://www.owasp.org/index.php/Testing_for_Error_Code_%28OWASP-IG-006%29
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking for Error codes"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveErrorMessagesLnk')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
