"""
GREP Plugin for Cookies Attributes
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Searches transaction DB for Cookie attributes"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString(
        "This plugin looks for cookie setting headers (TODO: Check vuln scanners' output!)<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_COOKIES')
    return Content
