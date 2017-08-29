"""
PASSIVE Plugin for HTTP Methods Testing
"""

from owtf.utils import OWTFLogger
from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Third party resources"


def run(PluginInfo):
    # Vuln search box to be built in core and resued in different plugins:
    resource = ServiceLocator.get_component("resource").get_resources('PassiveMethods')
    Content = ServiceLocator.get_component("plugin_helper").resource_linklist('Online Resources', resource)
    OWTFLogger.log("Passive links generated for target")
    return Content
