from framework.dependency_management.dependency_resolver import ServiceLocator
"""
Plugin for probing smtp
"""

DESCRIPTION = " SMTP Probing "

def run(PluginInfo):
    #ServiceLocator.get_component("config").Show()
    #print "Content="+Content
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('SmtpProbeMethods'), PluginInfo, []) # No previous output
