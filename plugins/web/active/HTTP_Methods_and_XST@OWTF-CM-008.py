from framework.dependency_management.dependency_resolver import ServiceLocator

"""
ACTIVE Plugin for Testing for HTTP Methods and XST (OWASP-CM-008)
"""

from framework.lib.general import get_random_str


DESCRIPTION = "Active probing for HTTP methods"


def run(PluginInfo):
    # Transaction = Core.Requester.TRACE(Core.Config.Get('host_name'), '/')
    target = ServiceLocator.get_component("target")
    URL = target.Get('top_url')
    # TODO: PUT not working right yet
    # PUT_URL = URL+"/_"+get_random_str(20)+".txt"
    # print PUT_URL
    # PUT_URL = URL+"/a.txt"
    # PUT_URL = URL
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.TransactionTableForURL(
        True,
        URL,
        Method='TRACE')
    # Content += Core.PluginHelper.TransactionTableForURL(
    #    True,
    #    PUT_URL,
    #    Method='PUT',
    #    Data=get_random_str(15))
    resource = ServiceLocator.get_component("resource")
    Content += plugin_helper.CommandDump(
        'Test Command',
        'Output',
        resource.GetResources('ActiveHTTPMethods'),
        PluginInfo,
        Content)
    return Content
