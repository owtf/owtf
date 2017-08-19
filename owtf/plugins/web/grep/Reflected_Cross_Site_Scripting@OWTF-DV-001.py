"""
GREP Plugin for XSS
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Searches transaction DB for XSS protections"


def run(PluginInfo):
    # Background: http://jeremiahgrossman.blogspot.com/2010/01/to-disable-ie8s-xss-filter-or-not.html
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    title = "This plugin looks for server-side protection headers against XSS (TODO: Check vuln scanners' output!)<br/>"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseHeaderMatchesForRegexpName('HEADERS_FOR_XSS_PROTECTION')
    return Content
