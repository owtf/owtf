from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Tools to assist credential transport vulnerability exploitation"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('ExternalCredentialsTransport')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
