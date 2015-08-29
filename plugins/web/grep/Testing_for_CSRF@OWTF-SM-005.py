from framework.dependency_management.dependency_resolver import ServiceLocator
"""
GREP Plugin for Testing for CSRF (OWASP-SM-005)
https://www.owasp.org/index.php/Testing_for_CSRF_%28OWASP-SM-005%29
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for CSRF protections"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	return ServiceLocator.get_component("plugin_helper").FindResponseBodyMatchesForRegexpName('RESPONSE_REGEXP_FOR_HIDDEN')
