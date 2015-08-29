from framework.dependency_management.dependency_resolver import ServiceLocator

"""
SEMI-PASSIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""

import string, re
import cgi

DESCRIPTION = "Normal requests to gather fingerprint info"

def run(PluginInfo):
    #Core.Config.Show()
    # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    TransactionTable = plugin_helper.TransactionTableForURLList(True, ServiceLocator.get_component("target").GetAsList(['target_url', 'top_url'])) 
    Content = plugin_helper.ResearchFingerprintInlog() + TransactionTable
    Content += plugin_helper.CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('SemiPassiveFingerPrint'), PluginInfo, Content)
    return Content

