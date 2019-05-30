"""
ACTIVE Plugin for Old, Backup and Unreferenced Files (OWASP-CM-006)
https://www.owasp.org/index.php/Testing_for_Old,_Backup_and_Unreferenced_Files_(OWASP-CM-006)
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper
from owtf.settings import INTERACTIVE

DESCRIPTION = "Active probing for juicy files (DirBuster)"


def run(PluginInfo):
    # Define DirBuster Commands to use depending on Interaction Setting:
    # DirBuster allows much more control when interactive
    # DirBuster can also be run non-interactively for scripting
    DirBusterInteraction = {
        "True": "DirBusterInteractive", "False": "DirBusterNotInteractive"
    }

    # Get settings from the config DB
    resource = get_resources(DirBusterInteraction["{}".format(INTERACTIVE)])
    Content = plugin_helper.CommandDump(
        "Test Command", "Output", resource, PluginInfo, []
    )
    extractURL_resource = get_resources("DirBuster_Extract_URLs")
    Content += plugin_helper.CommandDump(
        "Test Command", "Output", extractURL_resource, PluginInfo, []
    )
    return Content
