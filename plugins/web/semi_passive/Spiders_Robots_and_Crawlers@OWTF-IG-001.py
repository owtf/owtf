"""
Robots.txt semi-passive plugin, parses robots.txt file to generate on-screen
links and save them for later spidering and analysis
"""

from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Normal request for robots.txt analysis"


def run(PluginInfo):
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    target = ServiceLocator.get_component("target")
    requester = ServiceLocator.get_component("requester")
    top_url = target.Get('top_url')
    url = top_url + "/robots.txt"
    test_result = []
    # Use transaction cache if possible for speed
    http_transaction = requester.GetTransaction(True, url, "GET")
    if http_transaction is not None and http_transaction.Found:
        test_result += plugin_helper.ProcessRobots(
            PluginInfo,
            http_transaction.GetRawResponseBody(),
            top_url,
            '')
    else:  # robots.txt NOT found
        OWTFLogger.log("robots.txt was NOT found")
        test_result += plugin_helper.TransactionTableForURLList(True, [url])
    return test_result
