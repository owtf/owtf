from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Plugin to assist passive testing for known XSS vectors"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveCrossSiteScripting')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    return Content
