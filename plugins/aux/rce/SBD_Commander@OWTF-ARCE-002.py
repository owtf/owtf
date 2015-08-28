from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Runs commands on an agent server via SBD -i.e. for IDS testing-"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Core = ServiceLocator.get_component("core")
    Content = DESCRIPTION + " Results:<br />"
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    for Args in plugin_params.GetArgs({
                                                                          'Description': DESCRIPTION,
                                                                          'Mandatory': {
                                                                          'RHOST': config.Get('RHOST_DESCRIP'),
                                                                          'SBD_PORT': config.Get('SBD_PORT_DESCRIP'),
                                                                          'SBD_PASSWORD': config.Get('SBD_PASSWORD_DESCRIP'),
                                                                          'COMMAND_FILE': config.Get('COMMAND_FILE_DESCRIP')
                                                                          },
                                                                          'Optional': {
                                                                          'REPEAT_DELIM': config.Get('REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the aux plugin arguments as config

        #print "Args="+str(Args)
        Core.RemoteShell.Open({
                              'ConnectVia': config.GetResources('RCE_SBD_Connection')
                              , 'InitialCommands': None
                              }, PluginInfo)
        Core.RemoteShell.RunCommandList(Core.GetFileAsList(Args['COMMAND_FILE']))
        Core.RemoteShell.Close(PluginInfo)
    #Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', ServiceLocator.get_component("config").GetResources('LaunchExploit_'+Args['CATEGORY']+"_"+Args['SUBCATEGORY']), PluginInfo, "") # No previous output
    return Content
