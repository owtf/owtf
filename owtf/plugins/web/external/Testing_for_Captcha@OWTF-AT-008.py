"""
EXTERNAL Plugin for CAPTCHA assistance
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfo):
    Content = plugin_helper.VulnerabilitySearchBox("")
    resource = get_resources("ExternalCAPTCHA")
    Content += plugin_helper.resource_linklist("Tools", resource)
    return Content
