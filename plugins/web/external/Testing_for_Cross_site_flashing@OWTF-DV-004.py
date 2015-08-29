from framework.dependency_management.dependency_resolver import ServiceLocator
import string, re
import cgi

DESCRIPTION = "Cross Site Flashing Plugin to assist manual testing"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources',
                                                                             ServiceLocator.get_component(
                                                                                 "resource").GetResources(
                                                                                 'ExternalCrossSiteFlashing'))
    return Content

