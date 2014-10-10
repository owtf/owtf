from framework.utils import OWTFLogger
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

"""
import logging

DESCRIPTION = "Sends a bunch of URLs through selenium"
CATEGORIES = ['RCE', 'SQLI', 'XSS', 'CHARSET']


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()

    config = ServiceLocator.get_component("config")
    OWTFLogger.log("WARNING: This plugin requires a small selenium installation, please run '" + config.Get('INSTALL_SCRIPT') + "' if you have issues")
    Content = DESCRIPTION + " Results:<br />"

    plugin_params = ServiceLocator.get_component("plugin_params")
    for Args in plugin_params.GetArgs({
                                          'Description': DESCRIPTION,
                                          'Mandatory': {
                                              'BASE_URL': 'The URL to be pre-pended to the tests',
                                              'CATEGORY': 'Category to use (i.e. ' + ', '.join(sorted(CATEGORIES)) + ')'
                                          },
                                          'Optional': {
                                              'REPEAT_DELIM': config.Get(
                                                      'REPEAT_DELIM_DESCRIP')
                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)
    # print "Args="+str(Args)
    InputFile = config.Get("SELENIUM_URL_VECTORS_" + Args['CATEGORY'])
    URLLauncher = ServiceLocator.get_component("selenium_handler").CreateURLLauncher(
        {'BASE_URL': Args['BASE_URL'], 'INPUT_FILE': InputFile})
    URLLauncher.Run()
    return Content

