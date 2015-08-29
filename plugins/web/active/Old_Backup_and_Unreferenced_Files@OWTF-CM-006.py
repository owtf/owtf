from framework.dependency_management.dependency_resolver import ServiceLocator
""" 
ACTIVE Plugin for Old, Backup and Unreferenced Files (OWASP-CM-006)
https://www.owasp.org/index.php/Testing_for_Old,_Backup_and_Unreferenced_Files_(OWASP-CM-006)
"""

DESCRIPTION = "Active probing for juicy files (DirBuster)"

def run(PluginInfo):
	#ServiceLocator.get_component("config").Show()
	# Define DirBuster Commands to use depending on Interaction Setting:
	# DirBuster allows much more control when interactive
	# DirBuster can also be run non-interactively for scripting
	DirBusterInteraction = { 'true' : 'DirBusterInteractive', 'false' : 'DirBusterNotInteractive' }
	return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResourceList([ DirBusterInteraction[ServiceLocator.get_component("db_config").Get('INTERACTIVE')], 'DirBuster_Extract_URLs' ]), PluginInfo, [])
	#return ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', ServiceLocator.get_component("config").GetResources(DirBusterInteraction[ServiceLocator.get_component("config").Get('Interactive')]), PluginInfo, Content)

