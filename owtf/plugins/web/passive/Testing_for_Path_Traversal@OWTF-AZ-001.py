"""
PASSIVE Plugin
"""
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Panoptic, a tool for testing local file inclusion vulnerabilities"


def run(PluginInfo):
    Content = plugin_helper.SuggestedCommandBox(
        PluginInfo,
        [["All", "Testing_for_Path_Traversal_All"]],
        "Testing_for_Path_Traversal - Potentially useful commands",
    )
    return Content
