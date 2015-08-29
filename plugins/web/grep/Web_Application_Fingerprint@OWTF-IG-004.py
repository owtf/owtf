from framework.dependency_management.dependency_resolver import ServiceLocator
"""
GREP Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

DESCRIPTION = "Searches transaction DB for fingerprint traces"

def run(PluginInfo):
	Content = ServiceLocator.get_component("plugin_helper").ResearchFingerprintInlog()
	return Content
