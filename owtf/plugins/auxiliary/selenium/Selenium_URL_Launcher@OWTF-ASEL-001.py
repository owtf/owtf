from owtf.utils import OWTFLogger
from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Sends a bunch of URLs through selenium"
CATEGORIES = ['RCE', 'SQLI', 'XSS', 'CHARSET']


def run(PluginInfo):
    Content = []
    config = ServiceLocator.get_component("config")
    OWTFLogger.log("WARNING: This plugin requires a small selenium installation, please run '%s' if you have issues" %
                   config.get_val('INSTALL_SCRIPT'))
    plugin_params = ServiceLocator.get_component("plugin_params")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'BASE_URL': 'The URL to be pre-pended to the tests',
            'CATEGORY': 'Category to use (i.e. ' + ', '.join(sorted(CATEGORIES)) + ')'
        },
        'Optional': {'REPEAT_DELIM': config.get_val('REPEAT_DELIM_DESCRIP')}
    }

    for Args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(Args)
        InputFile = config.get_val("SELENIUM_URL_VECTORS_" + Args['CATEGORY'])
        URLLauncher = ServiceLocator.get_component("selenium_handler").CreateURLLauncher({
            'BASE_URL': Args['BASE_URL'],
            'INPUT_FILE': InputFile
        })
        URLLauncher.run()
    return Content
