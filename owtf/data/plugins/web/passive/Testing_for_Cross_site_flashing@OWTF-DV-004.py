"""
PASSIVE Plugin for Testing for Cross site flashing (OWASP-DV-004)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking for Cross Site Flashing"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveCrossSiteFlashingLnk')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
