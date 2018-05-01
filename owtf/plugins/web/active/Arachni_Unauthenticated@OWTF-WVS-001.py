"""
ACTIVE Plugin for Generic Unauthenticated Web App Fuzzing via Arachni
This will perform a "low-hanging-fruit" pass on the web app for easy to find (tool-findable) vulns

"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active Vulnerability Scanning without credentials via Arachni"


def run(PluginInfo):
    resource = get_resources("Arachni_Unauth")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])
