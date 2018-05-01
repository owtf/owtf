"""
GREP Plugin for Testing for application configuration management (OWASP-CM-004) <- looks for HTML Comments
https://www.owasp.org/index.php/Testing_for_application_configuration_management_%28OWASP-CM-004%29
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Searches transaction DB for SSI directives"


def run(PluginInfo):
    return plugin_helper.FindResponseBodyMatchesForRegexpName("RESPONSE_REGEXP_FOR_SSI")
