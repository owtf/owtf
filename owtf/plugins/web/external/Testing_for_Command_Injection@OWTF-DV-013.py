from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfo):
    resource = get_resources("ExternalCommandInjection")
    Content = plugin_helper.resource_linklist("Online Resources", resource)
    return Content
