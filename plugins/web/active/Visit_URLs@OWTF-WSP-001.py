from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator
""" 
This plugin does not perform ANY test: The aim is to visit all URLs grabbed so far and build the transaction log to feed data to other plugins
NOTE: This is an active plugin because it may visit URLs retrieved by vulnerability scanner spiders which may be considered sensitive or include vulnerability probing
"""

DESCRIPTION = "Visit URLs found by other tools, some could be sensitive: need permission"

def run(PluginInfo):
    #ServiceLocator.get_component("config").Show()
    urls = ServiceLocator.get_component("url_manager").GetURLsToVisit()
    for url in urls: # This will return only unvisited urls
        ServiceLocator.get_component("requester").GetTransaction(True, url) # Use cache if possible
    Content = str(len(urls))+" URLs were visited"
    OWTFLogger.log(Content)
    return ServiceLocator.get_component("plugin_helper").HtmlString(Content)
