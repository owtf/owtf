"""
Cross Site Flashing semi passive plugin: Tries to retrieve the crossdomain.xml
file and display it for review
"""
from owtf.requester.base import requester
from owtf.managers.target import get_targets_as_list
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Normal requests for XSF analysis"


def run(PluginInfo):
    url_list = []
    files = ["crossdomain.xml", "clientaccesspolicy.xml"]
    for url in get_targets_as_list(["target_url", "top_url"])[0]:
        for file in files:
            net_url = str(url + "/" + file)
            url_list.append(net_url)  # Compute all URL + File combinations
    # The requester owtf component will unique the URLs
    TransactionList = requester.get_transactions(True, url_list)
    # Even though we have transaction list, those transactions do not have id
    # because our proxy stores the transactions and not the requester. So the
    # best way is to use the url list to retrieve transactions while making the
    # report
    return plugin_helper.TransactionTableForURLList(True, url_list, "GET")
