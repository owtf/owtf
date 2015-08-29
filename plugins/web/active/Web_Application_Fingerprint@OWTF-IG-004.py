from framework.dependency_management.dependency_resolver import ServiceLocator
"""
ACTIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
https://www.owasp.org/index.php/Testing_for_Web_Application_Fingerprint_%28OWASP-IG-004%29
"""

DESCRIPTION = "Active probing for fingerprint analysis"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('ActiveFingerPrint'), PluginInfo, []) # No previous output
	return Content

