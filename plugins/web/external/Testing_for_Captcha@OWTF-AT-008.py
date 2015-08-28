from framework.dependency_management.dependency_resolver import ServiceLocator

"""
EXTERNAL Plugin for CAPTCHA assistance
"""

import string, re
import cgi

DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.VulnerabilitySearchBox('')
    Content += plugin_helper.ResourceLinkList('Tools', ServiceLocator.get_component("resource").GetResources('ExternalCAPTCHA'))
    return Content

