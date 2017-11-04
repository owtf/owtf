from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ExternalBypassingAuthorisationSchema')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
