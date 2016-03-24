"""
EXTERNAL Plugin for CAPTCHA assistance
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.VulnerabilitySearchBox('')
    Content += plugin_helper.ResourceLinkList(
        'Tools',
        ServiceLocator.get_component("resource").GetResources('ExternalCAPTCHA'))
    return Content
