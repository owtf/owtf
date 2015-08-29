from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Testing for Captcha (OWASP-AT-008)
"""

DESCRIPTION = "Google Hacking for CAPTCHA"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveCAPTCHALnk'))
	return Content

