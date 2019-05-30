"""
GREP Plugin for ClickJacking
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Searches transaction DB for Clickjacking protections"


def run(PluginInfo):
    title = "This plugin looks for server-side protection headers against Clickjacking" + "(TODO: Add rudimentary search for frame busting)<br/>"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName(
        "HEADERS_FOR_CLICKJACKING_PROTECTION"
    )
    return Content
