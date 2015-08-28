from framework.dependency_management.dependency_resolver import ServiceLocator
""" 
SEMI-PASSIVE Plugin for Search engine discovery/reconnaissance (OWASP-IG-002)
"""


DESCRIPTION = "Metadata analysis"
ATTR = {
    'INTERNET_RESOURCES': True,
}


def run(PluginInfo):
    #ServiceLocator.get_component("config").Show()
    Content = ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('SemiPassiveSearchEngineDiscoveryCmd'), PluginInfo, []) # No previous output
    return Content
