"""
PASSIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""

from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Third party resources and fingerprinting suggestions"


def run(PluginInfo):
    mapping = [
        ['All', 'CMS_FingerPrint_All'],
        ['WordPress', 'CMS_FingerPrint_WordPress'],
        ['Joomla', 'CMS_FingerPrint_Joomla'],
        ['Drupal', 'CMS_FingerPrint_Drupal'],
        ['Mambo', 'CMS_FingerPrint_Mambo']
    ]
    # Vuln search box to be built in core and reused in different plugins:
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.VulnerabilitySearchBox('')
    resource = ServiceLocator.get_component("resource").GetResources('PassiveFingerPrint')
    Content += plugin_helper.ResourceLinkList('Online Resources', resource)
    Content += plugin_helper.SuggestedCommandBox(PluginInfo, mapping, 'CMS Fingerprint - Potentially useful commands')
    return Content
