"""
ACTIVE Plugin for Testing for HTTP Methods and XST (OWASP-CM-008)
"""
from owtf.managers.resource import get_resources
from owtf.managers.target import target_manager
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active probing for HTTP methods"


def run(PluginInfo):
    URL = target_manager.get_val("top_url")
    # TODO: PUT not working right yet
    Content = plugin_helper.TransactionTableForURL(True, URL, Method="TRACE")
    Content += plugin_helper.CommandDump(
        "Test Command",
        "Output",
        get_resources("ActiveHTTPMethods"),
        PluginInfo,
        Content,
    )
    return Content
