"""
PASSIVE Plugin for HTTP Methods Testing
"""

from owtf.utils import OWTFLogger
from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Third party resources"


def run(PluginInfo):
    # Vuln search box to be built in core and resued in different plugins:
    resource = ServiceLocator.get_component("resource").GetResources('PassiveMethods')
    Content = ServiceLocator.get_component("plugin_helper").ResourceLinkList('Online Resources', resource)
    OWTFLogger.log("Passive links generated for target")
    return Content
