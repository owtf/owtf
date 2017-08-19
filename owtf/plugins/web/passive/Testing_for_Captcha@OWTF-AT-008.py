"""
PASSIVE Plugin for Testing for Captcha (OWASP-AT-008)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking for CAPTCHA"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").GetResources('PassiveCAPTCHALnk')
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', resource)
    return Content
