"""
SEMI-PASSIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Normal requests to gather fingerprint info"


def run(PluginInfo):
    # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    TransactionTable = plugin_helper.TransactionTableForURLList(True, ServiceLocator.get_component("target").GetAsList(
        ['target_url', 'top_url']))
    resource = ServiceLocator.get_component("resource").GetResources('SemiPassiveFingerPrint')
    Content = plugin_helper.ResearchFingerprintInlog() + TransactionTable
    Content += plugin_helper.CommandDump('Test Command', 'Output', resource, PluginInfo, Content)
    return Content
