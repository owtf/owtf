from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Runs commands on an agent server via SSH -i.e. for IDS testing-"
CHANNEL = 'SSH'


def run(PluginInfo):
    Core = ServiceLocator.get_component("core")
    Content = DESCRIPTION + " Results:<br />"
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'RHOST': config.Get('RHOST_DESCRIP'),
            'RUSER': config.Get('RUSER_DESCRIP'),
            'COMMAND_FILE': config.Get('COMMAND_FILE_DESCRIP')
        },
        'Optional': {
            'RPORT': config.Get('RPORT_DESCRIP'),
            'PASSPHRASE': config.Get('PASSPHRASE_DESCRIP'),
            'REPEAT_DELIM': config.Get('REPEAT_DELIM_DESCRIP')}
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the auxiliary plugin arguments as config

        Core.RemoteShell.Open({
            'ConnectVia': config.GetResources('RCE_SSH_Connection'),
            'InitialCommands': Args['PASSPHRASE']
        }, PluginInfo)
        Core.RemoteShell.Close(PluginInfo)
    resource = ServiceLocator.get_component("config").GetResources('LaunchExploit_' + Args['CATEGORY'] + "_" +
                                                                   Args['SUBCATEGORY'])
    Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', resource,
                                                                             PluginInfo, "")
    return Content
