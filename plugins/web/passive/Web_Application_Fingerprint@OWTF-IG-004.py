from framework.dependency_management.dependency_resolver import ServiceLocator

"""
PASSIVE Plugin for Testing for Web Application Fingerprint (OWASP-IG-004)
"""

DESCRIPTION = "Third party resources and fingerprinting suggestions"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    #Vuln search box to be built in core and reused in different plugins:
    plugin_helper = ServiceLocator.get_component("plugin_helper")
    Content = plugin_helper.VulnerabilitySearchBox('')
    Content += plugin_helper.ResourceLinkList('Online Resources', ServiceLocator.get_component("resource").GetResources('PassiveFingerPrint'))
    Content += plugin_helper.SuggestedCommandBox(PluginInfo,
                                                                                 [['All', 'CMS_FingerPrint_All'],
                                                                                  ['WordPress',
                                                                                   'CMS_FingerPrint_WordPress'],
                                                                                  ['Joomla', 'CMS_FingerPrint_Joomla'],
                                                                                  ['Drupal', 'CMS_FingerPrint_Drupal'],
                                                                                  ['Mambo', 'CMS_FingerPrint_Mambo']],
                                                                                 'CMS Fingerprint - Potentially useful commands')
    return Content

