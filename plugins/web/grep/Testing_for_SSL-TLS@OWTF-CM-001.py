"""
GREP Plugin for SSL protection
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Searches transaction DB for SSL protections"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    title = "This plugin looks for server-side protection headers to enforce SSL<br />"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_SSL_PROTECTION')
    return Content
