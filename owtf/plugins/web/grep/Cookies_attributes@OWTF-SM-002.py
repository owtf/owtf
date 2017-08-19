"""
GREP Plugin for Cookies Attributes
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Searches transaction DB for Cookie attributes"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    title = "This plugin looks for cookie setting headers (TODO: Check vuln scanners' output!)<br />"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_COOKIES')
    # TODO: Fix up
    return Content
