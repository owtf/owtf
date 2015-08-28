from framework.dependency_management.dependency_resolver import ServiceLocator

"""
GREP Plugin for Cookies Attributes
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi
import logging

DESCRIPTION = "Searches transaction DB for Cookie attributes"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString("This plugin looks for cookie setting headers (TODO: Check vuln scanners' output!)<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_COOKIES')
    # TODO: Fix up
    # AttributeAnalysis = ServiceLocator.get_component("plugin_helper").CookieAttributeAnalysis(AllValues, Header2TransacDict)
    return Content
