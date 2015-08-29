from framework.dependency_management.dependency_resolver import ServiceLocator
""" 
ACTIVE Plugin for Testing for Application Discovery (OWASP-IG-005)
"""

DESCRIPTION = "Active probing for app discovery"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('ActiveDiscovery'), PluginInfo, []) # No previous output
