from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for HTTP Methods Testing
"""
import logging
DESCRIPTION = "Third party resources"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	#Vuln search box to be built in core and resued in different plugins:
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveMethods'))
	OWTFLogger.log("Passive links generated for target")
	return Content

