from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing for Error Code (OWASP-IG-006)
https://www.owasp.org/index.php/Testing_for_Error_Code_%28OWASP-IG-006%29
"""

DESCRIPTION = "Google Hacking for Error codes"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveErrorMessagesLnk'))
	return Content

