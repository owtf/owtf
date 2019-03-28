"""
GREP Plugin for Spiders,Crawlers and Robots
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Searches transaction DB for Robots meta tag and X-Robots-Tag HTTP header"


def run(PluginInfo):
    title = "This plugin looks for Robots meta tag and X-Robots-Tag HTTP header<br />"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName(
        "HEADERS_FOR_ROBOTS"
    )
    Content += plugin_helper.FindResponseBodyMatchesForRegexpName(
        "RESPONSE_REGEXP_FOR_ROBOTS_META_TAG"
    )
    return Content
