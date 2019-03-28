"""
ACTIVE Plugin for Unauthenticated Nikto testing
This will perform a "low-hanging-fruit" pass on the web app for easy to find (tool-findable) vulns
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active Vulnerability Scanning without credentials via nikto"


def run(PluginInfo):
    NiktoOutput = plugin_helper.CommandDump(
        "Test Command", "Output", get_resources("Nikto_Unauth"), PluginInfo, []
    )
    Content = plugin_helper.CommandDump(
        "Test Command",
        "Output",
        get_resources("Nikto_Verify_Unauth"),
        PluginInfo,
        NiktoOutput,
    )
    return Content + NiktoOutput  # Show Nikto Verify FIRST (more useful, with links to findings, etc)
