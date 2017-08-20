from owtf.dependency_management.dependency_resolver import ServiceLocator
from owtf.lib.general import get_file_as_list


DESCRIPTION = "Runs commands on an agent server via SBD -i.e. for IDS testing-"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'RHOST': config.FrameworkConfigGet('RHOST_DESCRIP'),
            'SBD_PORT': config.FrameworkConfigGet('SBD_PORT_DESCRIP'),
            'SBD_PASSWORD': config.FrameworkConfigGet('SBD_PASSWORD_DESCRIP'),
            'COMMAND_FILE': config.FrameworkConfigGet('COMMAND_FILE_DESCRIP')
        },
        'Optional': {'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')}
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the auxiliary plugin arguments as config
        ServiceLocator.get_component("interactive_shell").Open({
            'ConnectVia': ServiceLocator.get_component("resource").get_resources('RCE_SBD_Connection'),
            'InitialCommands': None,
            'ExitMethod': Args['ISHELL_EXIT_METHOD'],
            'CommandsBeforeExit': Args['ISHELL_COMMANDS_BEFORE_EXIT'],
            'CommandsBeforeExitDelim': Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM'],
            'RHOST': Args['RHOST'],
            'RPORT': Args['SBD_PORT']
        }, PluginInfo)
        Content += ServiceLocator.get_component("interactive_shell").RunCommandList(get_file_as_list(
            Args['COMMAND_FILE']), PluginInfo)
    if not ServiceLocator.get_component("interactive_shell").IsClosed():  # Ensure clean exit if reusing connection
        ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
    return Content
