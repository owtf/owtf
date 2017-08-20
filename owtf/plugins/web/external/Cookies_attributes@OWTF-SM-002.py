from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Cookie Attributes Plugin to assist manual testing"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ExternalCookiesAttributes')
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Hash Cracking Resources', resource)
    return Content
