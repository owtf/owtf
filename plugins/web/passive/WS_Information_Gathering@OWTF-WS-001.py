from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing: WS Information Gathering (OWASP-WS-001)
"""
import logging
DESCRIPTION = "Google Hacking/Third party sites for Web Services"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	return ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('WSPassiveSearchEngineDiscoveryLnk'))
