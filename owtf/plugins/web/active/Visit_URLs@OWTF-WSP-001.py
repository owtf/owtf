"""
This plugin does not perform ANY test: The aim is to visit all URLs grabbed so far and build
the transaction log to feed data to other plugins
NOTE: This is an active plugin because it may visit URLs retrieved by vulnerability scanner spiders
which may be considered sensitive or include vulnerability probing
"""
import logging

from owtf.requester.base import requester
from owtf.managers.url import get_urls_to_visit
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Visit URLs found by other tools, some could be sensitive: need permission"


def run(PluginInfo):
    urls = get_urls_to_visit()
    for url in urls:  # This will return only unvisited urls
        requester.get_transaction(True, url)  # Use cache if possible
    Content = "{} URLs were visited".format(str(len(urls)))
    logging.info(Content)
    return plugin_helper.HtmlString(Content)
