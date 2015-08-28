from framework.dependency_management.dependency_resolver import ServiceLocator

"""
GREP Plugin for SSL protection
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for SSL protections"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString("This plugin looks for server-side protection headers to enforce SSL<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_SSL_PROTECTION')
    return Content
