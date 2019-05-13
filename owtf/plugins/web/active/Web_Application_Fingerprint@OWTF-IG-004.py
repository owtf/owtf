"""
ACTIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
https://www.owasp.org/index.php/Testing_for_Web_Application_Fingerprint_%28OWASP-IG-004%29
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active probing for fingerprint analysis"


def run(PluginInfo):
    resource = get_resources("ActiveFingerPrint")
    Content = plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )  # No previous output
    return Content
