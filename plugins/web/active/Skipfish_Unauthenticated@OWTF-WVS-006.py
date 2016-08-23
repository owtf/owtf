"""
ACTIVE Plugin for Generic Unauthenticated Web App Fuzzing via Skipfish
This will perform a "low-hanging-fruit" pass on the web app for easy to find (tool-findable) vulns
"""

from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.db.plugin_uploader import PluginUploader


DESCRIPTION = "Active Vulnerability Scanning without credentials via Skipfish"


def run(PluginInfo):
    target = ServiceLocator.get_component("target")
    resource = ServiceLocator.get_component("resource").GetResources('Skipfish_Unauth')
    Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output',
                                                                     resource, PluginInfo, [])
    plugin_output_dir = target.GetPath('plugin_output_dir') + '/skipfish_report'
    pUploader = PluginUploader('skipfish')
    pUploader.init_uploader(plugin_output_dir)
    pUploader.OWTFDBUpload()
    return Content
