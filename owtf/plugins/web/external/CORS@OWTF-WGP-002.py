"""
Plugin for manual/external CORS testing
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "CORS Plugin to assist manual testing"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ExternalCORS')
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', resource)
    return Content
