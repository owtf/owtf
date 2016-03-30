"""
ACTIVE Plugin for Generic Unauthenticated Web App Fuzzing via Arachni
This will perform a "low-hanging-fruit" pass on the web app for easy to find (tool-findable) vulns
"""

from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Active Vulnerability Scanning without credentials via Arachni"


def run(PluginInfo):
    return ServiceLocator.get_component("plugin_helper").CommandDump(
        'Test Command',
        'Output',
        ServiceLocator.get_component("resource").GetResources('Arachni_Unauth'),
        PluginInfo, [])
