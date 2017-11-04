"""
ACTIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
https://www.owasp.org/index.php/Testing_for_Web_Application_Fingerprint_%28OWASP-IG-004%29
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Active probing for fingerprint analysis"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ActiveFingerPrint')
    Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                        resource, PluginInfo, [])  # No previous output
    return Content
