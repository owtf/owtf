from framework.dependency_management.dependency_resolver import ServiceLocator

"""
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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

