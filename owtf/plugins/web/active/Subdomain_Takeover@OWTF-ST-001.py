"""
ACTIVE Plugin which Test for Subdomain Takeover (OWASP-ST-001)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active plugin which Test for Subdomain Takeover"


def run(PluginInfo):
    resource = get_resources("SubdomainTakeover")
    Content = plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )
    return Content
