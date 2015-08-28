from framework.dependency_management.dependency_resolver import ServiceLocator
"""
PASSIVE Plugin
"""
DESCRIPTION = "Panoptic, a tool for testing local file inclusion vulnerabilities"
def run(PluginInfo):
         #ServiceLocator.get_component("config").Show()
         Content = ServiceLocator.get_component("plugin_helper").SuggestedCommandBox( PluginInfo, [ [ 'All', 'Testing_for_Path_Traversal_All' ]  ], 'Testing_for_Path_Traversal - Potentially useful commands' )
         return Content
