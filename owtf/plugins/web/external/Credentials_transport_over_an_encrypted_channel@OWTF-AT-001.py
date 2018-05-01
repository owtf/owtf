from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Tools to assist credential transport vulnerability exploitation"


def run(PluginInfo):
    resource = get_resources("ExternalCredentialsTransport")
    Content = plugin_helper.resource_linklist("Online Resources", resource)
    return Content
