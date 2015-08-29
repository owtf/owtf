from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing for Cross site flashing (OWASP-DV-004)
"""

DESCRIPTION = "Google Hacking for Cross Site Flashing"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveCrossSiteFlashingLnk'))
	return Content

