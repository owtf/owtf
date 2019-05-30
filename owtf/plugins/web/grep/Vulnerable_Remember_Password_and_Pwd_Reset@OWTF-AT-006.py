"""
GREP Plugin for Vulnerable Remember Password and Pwd Reset (OWASP-AT-006)
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Searches transaction DB for autocomplete protections"


def run(PluginInfo):
    title = "This plugin looks for password and form tags to review the autocomplete attribute<br />"
    Content = plugin_helper.HtmlString(title)
    Content += plugin_helper.FindResponseBodyMatchesForRegexpName(
        "RESPONSE_REGEXP_FOR_AUTOCOMPLETE"
    )
    return Content
