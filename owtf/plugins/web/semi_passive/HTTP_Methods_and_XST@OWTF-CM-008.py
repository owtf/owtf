"""
SEMI-PASSIVE Plugin for Testing for HTTP Methods and XST (OWASP-CM-008)
"""
from owtf.managers.resource import get_resources
from owtf.managers.target import get_targets_as_list
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Normal request for HTTP methods analysis"


def run(PluginInfo):
    resource = get_resources("SemiPassiveHTTPMethods")
    Content = plugin_helper.TransactionTableForURLList(
        True, get_targets_as_list(["target_url", "top_url"]), "OPTIONS"
    )
    # No previous output
    Content += plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )
    return Content
