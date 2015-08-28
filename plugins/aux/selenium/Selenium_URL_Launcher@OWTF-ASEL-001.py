from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator
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

