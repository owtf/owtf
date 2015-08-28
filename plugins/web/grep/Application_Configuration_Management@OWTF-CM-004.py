from framework.dependency_management.dependency_resolver import ServiceLocator
"""
GREP Plugin for Testing for application configuration management (OWASP-CM-004) <- looks for HTML Comments
https://www.owasp.org/index.php/Testing_for_application_configuration_management_%28OWASP-CM-004%29
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for comments"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").FindResponseBodyMatchesForRegexpNames(['RESPONSE_REGEXP_FOR_HTML_COMMENTS','RESPONSE_REGEXP_FOR_CSS_JS_COMMENTS','RESPONSE_REGEXP_FOR_JS_COMMENTS', 'RESPONSE_REGEXP_FOR_PHP_SOURCE', 'RESPONSE_REGEXP_FOR_ASP_SOURCE'])
	return Content
