"""
PASSIVE Plugin for Old, Backup and Unreferenced Files (OWASP-CM-006)
https://www.owasp.org/index.php/Testing_for_Old,_Backup_and_Unreferenced_Files_(OWASP-CM-006)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Google Hacking for juicy files"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('PassiveOldBackupUnreferencedFilesLnk')
    return ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
