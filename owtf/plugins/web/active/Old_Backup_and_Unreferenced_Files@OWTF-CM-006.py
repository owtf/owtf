"""
ACTIVE Plugin for Old, Backup and Unreferenced Files (OWASP-CM-006)
https://www.owasp.org/index.php/Testing_for_Old,_Backup_and_Unreferenced_Files_(OWASP-CM-006)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Active probing for juicy files (DirBuster)"


def run(PluginInfo):
    # Define DirBuster Commands to use depending on Interaction Setting:
    # DirBuster allows much more control when interactive
    # DirBuster can also be run non-interactively for scripting
    DirBusterInteraction = {'true': 'DirBusterInteractive', 'false': 'DirBusterNotInteractive'}

    # Get settings from the config DB
    db_interactive = ServiceLocator.get_component("db_config").Get('INTERACTIVE')
    resource = ServiceLocator.get_component("resource").get_resources(DirBusterInteraction[db_interactive])
    Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                        PluginInfo, [])
    extractURL_resource = ServiceLocator.get_component("resource").get_resources('DirBuster_Extract_URLs')
    Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                         extractURL_resource, PluginInfo, [])
    return Content
