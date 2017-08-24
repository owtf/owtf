from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "XML Injection Plugin to assist manual testing"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ExternalXMLInjection')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
