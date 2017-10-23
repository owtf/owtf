"""
PASSIVE Plugin
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Panoptic, a tool for testing local file inclusion vulnerabilities"


def run(PluginInfo):
    Content = ServiceLocator.get_component("plugin_helper").SuggestedCommandBox(
        PluginInfo, [['All', 'Testing_for_Path_Traversal_All']],
        'Testing_for_Path_Traversal - Potentially useful commands')
    return Content
