"""
GREP Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Searches transaction DB for fingerprint traces"


def run(PluginInfo):
    Content = plugin_helper.ResearchFingerprintInlog()
    return Content
