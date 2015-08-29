from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing for SQL Injection (OWASP-DV-005)
https://www.owasp.org/index.php/Testing_for_SQL_Injection_%28OWASP-DV-005%29
"""

DESCRIPTION = "Google Hacking for SQLi"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveSQLInjectionLnk'))
	return Content

