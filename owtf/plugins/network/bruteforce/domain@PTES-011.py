"""
Plugin for probing DNS
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = " DNS Probing "


def run(PluginInfo):
    return plugin_helper.CommandDump(
        "Test Command", "Output", get_resources("DomainBruteForcing"), PluginInfo, ""
    )
