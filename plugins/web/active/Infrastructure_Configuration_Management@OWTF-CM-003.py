from framework.dependency_management.dependency_resolver import ServiceLocator
"""
ACTIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004) 
"""
import cgi

DESCRIPTION = "Active Probing for fingerprint analysis"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('ActiveInfrastructureConfigurationManagement'), PluginInfo, []) # No previous output
	return Content
