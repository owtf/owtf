from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Plugin to assist passive testing for known XSS vectors"


def run(PluginInfo):
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList(
        'Online Resources',
        ServiceLocator.get_component("resource").GetResources('PassiveCrossSiteScripting'))
    return Content
