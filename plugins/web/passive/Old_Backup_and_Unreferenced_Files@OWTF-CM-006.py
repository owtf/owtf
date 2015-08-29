from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin for Old, Backup and Unreferenced Files (OWASP-CM-006)
https://www.owasp.org/index.php/Testing_for_Old,_Backup_and_Unreferenced_Files_(OWASP-CM-006)
"""

DESCRIPTION = "Google Hacking for juicy files"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	return ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveOldBackupUnreferencedFilesLnk'))
