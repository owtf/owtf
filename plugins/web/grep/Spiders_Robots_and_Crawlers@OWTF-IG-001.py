from framework.dependency_management.dependency_resolver import ServiceLocator

"""
GREP Plugin for Spiders,Crawlers and Robots
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

import string, re
import cgi

DESCRIPTION = "Searches transaction DB for Robots meta tag and X-Robots-Tag HTTP header"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.HtmlString("This plugin looks for Robots meta tag and X-Robots-Tag HTTP header<br />")
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_ROBOTS')
    Content += plugin_helper.FindResponseBodyMatchesForRegexpName('RESPONSE_REGEXP_FOR_ROBOTS_META_TAG')
    return Content
