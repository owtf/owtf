from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Sends a bunch of URLs through selenium"
CATEGORIES = ['RCE', 'SQLI', 'XSS', 'CHARSET']

def run(PluginInfo):
    Content = []
    config = ServiceLocator.get_component("config")
    OWTFLogger.log("WARNING: This plugin requires a small selenium installation, please run '%s' if you have issues" %
                   config.FrameworkConfigGet('INSTALL_SCRIPT'))
    plugin_params = ServiceLocator.get_component("plugin_params")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'BASE_URL': 'The URL to be pre-pended to the tests',
            'CATEGORY': 'Category to use (i.e. ' + ', '.join(sorted(CATEGORIES)) + ')'
        },
        'Optional': {'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')}
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)
        InputFile = config.FrameworkConfigGet("SELENIUM_URL_VECTORS_" + Args['CATEGORY'])
        URLLauncher = ServiceLocator.get_component("selenium_handler").CreateURLLauncher({
                                                                            'BASE_URL': Args['BASE_URL'],
                                                                            'INPUT_FILE': InputFile
                                                                        })
        URLLauncher.Run()
    return Content

