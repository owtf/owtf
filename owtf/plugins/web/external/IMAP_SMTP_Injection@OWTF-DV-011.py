from framework.dependency_management.dependency_resolver import ServiceLocator



DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfo):
    Content = ServiceLocator.get_component("plugin_helper").HtmlString("Intended to show helpful info in the future")
    return Content
