"""
PASSIVE Plugin for Testing for Cross site flashing (OWASP-DV-004)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Google Hacking for Cross Site Flashing"


def run(PluginInfo):
    resource = get_resources("PassiveCrossSiteFlashingLnk")
    Content = plugin_helper.resource_linklist("Online Resources", resource)
    return Content
