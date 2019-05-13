"""
Robots.txt analysis
"""
import logging

from owtf.requester.base import requester
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "robots.txt analysis through third party sites"


def run(PluginInfo):
    Content = plugin_helper.Requestlink_list(
        "Passive Analysis Results",
        get_resources("PassiveRobotsAnalysisHTTPRequests"),
        PluginInfo,
    )
    Content += plugin_helper.resource_linklist(
        "Online Resources", get_resources("PassiveRobotsAnalysisLinks")
    )
    # Try to retrieve the robots.txt file from all defined resources
    Count = 0
    for Name, Resource in get_resources("PassiveRobots"):
        URL = Resource  # Just for clarity
        # Preparing link chunks for disallowed entries
        LinkStart, LinkFinish = URL.split("/robots.txt")
        LinkStart = LinkStart.strip()
        LinkFinish = LinkFinish.strip()
        # Use the cache if possible for speed
        Transaction = requester.get_transaction(True, URL)
        if Transaction is not None and Transaction.found:
            Content += plugin_helper.ProcessRobots(
                PluginInfo,
                Transaction.get_raw_response_body,
                LinkStart,
                LinkFinish,
                "robots%s.txt" % str(Count),
            )
            Count += 1
        else:  # Not found or unknown request error
            Message = "Could not be retrieved using resource: %s" % Resource
            logging.info(Message)
        Content += plugin_helper.TransactionTableForURLList(True, [URL])
    return Content
