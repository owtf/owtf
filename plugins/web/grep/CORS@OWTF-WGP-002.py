from framework.dependency_management.dependency_resolver import ServiceLocator

"""
GREP Plugin for CORS
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for Cross Origin Resource Sharing headers"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString("This plugin looks for HTML 5 Cross Origin Resource Sharing (CORS) headers<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_CORS')
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_REGEXP_FOR_CORS_METHODS')
    return Content
