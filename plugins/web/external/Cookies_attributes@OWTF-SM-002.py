from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Cookie Attributes Plugin to assist manual testing"


def run(PluginInfo):
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList(
        'Online Hash Cracking Resources',
        ServiceLocator.get_component("resource").GetResources('ExternalCookiesAttributes'))
    return Content
