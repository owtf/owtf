"""
PASSIVE Plugin for Testing for Captcha (OWASP-AT-008)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking for CAPTCHA"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveCAPTCHALnk')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
