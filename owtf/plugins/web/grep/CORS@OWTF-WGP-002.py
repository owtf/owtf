"""
GREP Plugin for CORS
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Searches transaction DB for Cross Origin Resource Sharing headers"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    title = "This plugin looks for HTML 5 Cross Origin Resource Sharing (CORS) headers<br/>"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_CORS')
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_REGEXP_FOR_CORS_METHODS')
    return Content
