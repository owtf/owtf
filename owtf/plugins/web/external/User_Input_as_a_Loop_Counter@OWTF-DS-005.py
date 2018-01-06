from owtf.plugin.plugin_helper import plugin_helper


DESCRIPTION = "Plugin to assist manual testing"


def run(PluginInfoz):
    Content = plugin_helper.HtmlString("Intended to show helpful info in the future")
    return Content
