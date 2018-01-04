from owtf.managers.resource import get_resources
from owtf.plugin.plugin_helper import plugin_helper


DESCRIPTION = "Cookie Attributes Plugin to assist manual testing"


def run(PluginInfo):
    resource = get_resources('ExternalCookiesAttributes')
    Content = plugin_helper.resource_linklist('Online Hash Cracking Resources', resource)
    return Content
