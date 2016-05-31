from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.lib.general import GetFileAsList

DESCRIPTION = "Runs commands on an agent server via SBD -i.e. for IDS testing-"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    for Args in plugin_params.GetArgs({
                                                                          'Description': DESCRIPTION,
                                                                          'Mandatory': {
                                                                          'RHOST': config.FrameworkConfigGet('RHOST_DESCRIP'),
                                                                          'SBD_PORT': config.FrameworkConfigGet('SBD_PORT_DESCRIP'),
                                                                          'SBD_PASSWORD': config.FrameworkConfigGet('SBD_PASSWORD_DESCRIP'),
                                                                          'COMMAND_FILE': config.FrameworkConfigGet('COMMAND_FILE_DESCRIP')
                                                                          },
                                                                          'Optional': {
                                                                          'ISHELL_EXIT_METHOD': config.FrameworkConfigGet('ISHELL_EXIT_METHOD_DESCRIP'),
                                                                          'ISHELL_DELAY_BETWEEN_COMMANDS': config.FrameworkConfigGet('ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
                                                                          'ISHELL_COMMANDS_BEFORE_EXIT': config.FrameworkConfigGet('ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
                                                                          'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.FrameworkConfigGet('ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
                                                                          'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the auxiliary plugin arguments as config
        ServiceLocator.get_component("interactive_shell").Open({
                              'ConnectVia': ServiceLocator.get_component("resource").GetResources('RCE_SBD_Connection'),
                              'InitialCommands': None,
                              'ExitMethod': Args['ISHELL_EXIT_METHOD'],
                              'CommandsBeforeExit': Args['ISHELL_COMMANDS_BEFORE_EXIT'],
                              'CommandsBeforeExitDelim': Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM'],
                              'RHOST': Args['RHOST'],
                              'RPORT': Args['SBD_PORT']
                              }, PluginInfo)
        ServiceLocator.get_component("interactive_shell").RunCommandList(GetFileAsList(Args['COMMAND_FILE']), PluginInfo)
    if not ServiceLocator.get_component("interactive_shell").IsClosed():  # Ensure clean exit if reusing connection
        ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
    return Content
