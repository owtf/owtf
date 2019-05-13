"""
SEMI-PASSIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""
from owtf.managers.resource import get_resources
from owtf.managers.target import get_targets_as_list
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Normal requests to gather fingerprint info"


def run(PluginInfo):
    # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
    TransactionTable = plugin_helper.TransactionTableForURLList(
        True, get_targets_as_list(["target_url", "top_url"])
    )
    resource = get_resources("SemiPassiveFingerPrint")
    Content = plugin_helper.ResearchFingerprintInlog() + TransactionTable
    Content += plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, Content
    )
    return Content
