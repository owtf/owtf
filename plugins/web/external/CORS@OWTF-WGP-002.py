from framework.dependency_management.dependency_resolver import ServiceLocator
"""
Plugin for manual/external CORS testing
"""

import string, re
import cgi

DESCRIPTION = "CORS Plugin to assist manual testing"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('ExternalCORS'))
	return Content
