"""
ACTIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""

from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Active Probing for fingerprint analysis"


def run(PluginInfo):
    # No previous output
    resource = ServiceLocator.get_component("resource").GetResources('ActiveInfrastructureConfigurationManagement')
    Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                        PluginInfo, [])
    return Content
