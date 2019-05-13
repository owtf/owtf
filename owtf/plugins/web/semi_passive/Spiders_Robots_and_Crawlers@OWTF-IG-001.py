"""
Robots.txt semi-passive plugin, parses robots.txt file to generate on-screen
links and save them for later spidering and analysis
"""
import logging

from owtf.requester.base import requester
from owtf.managers.target import target_manager
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Normal request for robots.txt analysis"


def run(PluginInfo):
    top_url = target_manager.get_val("top_url")
    url = "{}/robots.txt".format(top_url)
    test_result = []
    # Use transaction cache if possible for speed
    http_transaction = requester.get_transaction(True, url, "GET")
    if http_transaction is not None and http_transaction.found:
        test_result += plugin_helper.ProcessRobots(
            PluginInfo, http_transaction.get_raw_response_body, top_url, ""
        )
    else:  # robots.txt NOT found
        logging.info("robots.txt was NOT found")
        test_result += plugin_helper.TransactionTableForURLList(True, [url])
    return test_result
