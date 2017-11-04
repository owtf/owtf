"""
ACTIVE Plugin for Generic Unauthenticated Web App Fuzzing via w3af
This will perform a "low-hanging-fruit" pass on the web app for easy to find (tool-findable) vulns
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Active Vulnerability Scanning without credentials via w3af"


def run(PluginInfo):
    resource = ServiceLocator.get_component("resource").get_resources('W3AF_Unauth')
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                     resource, PluginInfo, [])
