from framework.dependency_management.dependency_resolver import ServiceLocator
"""
Plugin for probing x11
"""

DESCRIPTION = " x11 Probing "

def run(PluginInfo):
    #ServiceLocator.get_component("config").Show()
    #print "Content="+Content
    return ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('X11ProbeMethods'), PluginInfo, []) # No previous output
