from framework.dependency_management.dependency_resolver import ServiceLocator

"""
GREP Plugin for XSS
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for XSS protections"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    #Background: http://jeremiahgrossman.blogspot.com/2010/01/to-disable-ie8s-xss-filter-or-not.html
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString("This plugin looks for server-side protection headers against XSS (TODO: Check vuln scanners' output!)<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_XSS_PROTECTION')
    return Content
