from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing_for_SSI_Injection@OWASP-DV-009
"""

DESCRIPTION = "Searching for pages that are susceptible to SSI-Injection"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveSSIDiscoveryLnk'))
	return Content
