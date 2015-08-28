from framework.dependency_management.dependency_resolver import ServiceLocator

"""
GREP Plugin for Logout and Browse cache management
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for Cache snooping protections"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString("This plugin looks for server-side protection headers and tags against cache snooping<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_CACHE_PROTECTION')
    Content += plugin_helper.FindResponseBodyMatchesForRegexpName('RESPONSE_REGEXP_FOR_CACHE_PROTECTION')
    return Content
