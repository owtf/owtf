import time

from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Runs a chain of commands on an agent server via SBD -i.e. for IDS testing-"


def run(PluginInfo):
    Content = DESCRIPTION + " Results:<br />"
    Iteration = 1  # Iteration counter initialisation
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'RHOST': config.Get('RHOST_DESCRIP'),
            'SBD_PORT': config.Get('SBD_PORT_DESCRIP'),
            'SBD_PASSWORD': config.Get('SBD_PASSWORD_DESCRIP'),
            'COMMAND_PREFIX': 'The command string to be pre-pended to the tests (i.e. /usr/lib/firefox... http...)',
        },
        'Optional': {
            'TEST': 'The test to be included between prefix and suffix',
            'COMMAND_SUFIX': 'The URL to be appended to the tests (i.e. ...whatever)',
            'ISHELL_REUSE_CONNECTION': config.Get('ISHELL_REUSE_CONNECTION_DESCRIP'),
            'ISHELL_EXIT_METHOD': config.Get('ISHELL_EXIT_METHOD_DESCRIP'),
            'ISHELL_DELAY_BETWEEN_COMMANDS': config.Get('ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT': config.Get('ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.Get('ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
            'REPEAT_DELIM': config.Get('REPEAT_DELIM_DESCRIP')}
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the auxiliary plugin arguments as config
        REUSE_CONNECTION = (Args['ISHELL_REUSE_CONNECTION'] == 'yes')
        DELAY_BETWEEN_COMMANDS = Args['ISHELL_DELAY_BETWEEN_COMMANDS']
        if Iteration == 1 or not REUSE_CONNECTION:
            ServiceLocator.get_component("interactive_shell").Open({
                'ConnectVia': config.GetResources('RCE_SBD_Connection'),
                'InitialCommands': None,
                'ExitMethod': Args['ISHELL_EXIT_METHOD'],
                'CommandsBeforeExit': Args['ISHELL_COMMANDS_BEFORE_EXIT'],
                'CommandsBeforeExitDelim': Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM'],
                'RHOST': Args['RHOST'],
                'RPORT': Args['SBD_PORT']
            }, PluginInfo)
        else:
            OWTFLogger.log("Reusing initial connection..")
        ServiceLocator.get_component("interactive_shell").Run(
            Args['COMMAND_PREFIX'] + Args['TEST'] + Args['COMMAND_SUFIX'])
        OWTFLogger.log("Sleeping " + DELAY_BETWEEN_COMMANDS + " second(s) (increases reliability)..")
        time.sleep(int(DELAY_BETWEEN_COMMANDS))
        if not REUSE_CONNECTION:
            ServiceLocator.get_component("interactive_shell").Close(PluginInfo)

        resource = ServiceLocator.get_component("config").GetResources('LaunchExploit_' + Args['CATEGORY'] + "_" +
                                                                       Args['SUBCATEGORY'])
        Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', resource,
                                                                                 PluginInfo, "")  # No previous output
        Iteration += 1  # Increase Iteration counter
    if not ServiceLocator.get_component("interactive_shell").IsClosed():  # Ensure clean exit if reusing connection
        ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
    return Content
