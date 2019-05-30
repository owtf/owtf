"""
ACTIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active Probing for fingerprint analysis"


def run(PluginInfo):
    # No previous output
    resource = get_resources("ActiveInfrastructureConfigurationManagement")
    Content = plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )
    return Content
