import logging

from owtf.config import config_handler
from owtf.plugin.params import plugin_params

DESCRIPTION = "Sends a bunch of URLs through selenium"
CATEGORIES = ["RCE", "SQLI", "XSS", "CHARSET"]


def run(PluginInfo):
    Content = []
    logging.info(
        "WARNING: This plugin requires a small selenium installation, please run '%s' if you have issues"
        % config.get_val("INSTALL_SCRIPT")
    )

    args = {
        "Description": DESCRIPTION,
        "Mandatory": {
            "BASE_URL": "The URL to be pre-pended to the tests",
            "CATEGORY": "Category to use (i.e. " + ", ".join(sorted(CATEGORIES)) + ")",
        },
        "Optional": {"REPEAT_DELIM": config_handler.get_val("REPEAT_DELIM_DESCRIP")},
    }

    for args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(args)
        InputFile = config_handler.get_val("SELENIUM_URL_VECTORS_" + args["CATEGORY"])
        URLLauncher = ServiceLocator.get_component(
            "selenium_handler"
        ).CreateURLLauncher(
            {"BASE_URL": args["BASE_URL"], "INPUT_FILE": InputFile}
        )
        URLLauncher.run()
    return Content
