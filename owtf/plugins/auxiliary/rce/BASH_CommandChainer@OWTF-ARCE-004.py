import time

from owtf.utils import OWTFLogger
from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Runs a chain of commands on an agent server via SBD -i.e. for IDS testing-"


def run(PluginInfo):
    Content = []
    Iteration = 1  # Iteration counter initialisation
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'RHOST': config.get_val('RHOST_DESCRIP'),
            'SBD_PORT': config.get_val('SBD_PORT_DESCRIP'),
            'SBD_PASSWORD': config.get_val('SBD_PASSWORD_DESCRIP'),
            'COMMAND_PREFIX': 'The command string to be pre-pended to the tests (i.e. /usr/lib/firefox... http...)',
        },
        'Optional': {
            'TEST': 'The test to be included between prefix and suffix',
            'COMMAND_SUFFIX': 'The URL to be appended to the tests (i.e. ...whatever)',
            'ISHELL_REUSE_CONNECTION': config.get_val('ISHELL_REUSE_CONNECTION_DESCRIP'),
            'ISHELL_EXIT_METHOD': config.get_val('ISHELL_EXIT_METHOD_DESCRIP'),
            'ISHELL_DELAY_BETWEEN_COMMANDS': config.get_val('ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT': config.get_val('ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.get_val('ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
            'REPEAT_DELIM': config.get_val('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(Args)  # Sets the auxiliary plugin arguments as config
        REUSE_CONNECTION = (Args['ISHELL_REUSE_CONNECTION'] == 'yes')
        DELAY_BETWEEN_COMMANDS = Args['ISHELL_DELAY_BETWEEN_COMMANDS']
        if (Iteration == 1) or (not REUSE_CONNECTION):
            ServiceLocator.get_component("interactive_shell").Open({
                'ConnectVia': config.get_resources('RCE_SBD_Connection'),
                'InitialCommands': None,
                'ExitMethod': Args['ISHELL_EXIT_METHOD'],
                'CommandsBeforeExit': Args['ISHELL_COMMANDS_BEFORE_EXIT'],
                'CommandsBeforeExitDelim': Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM'],
                'RHOST': Args['RHOST'],
                'RPORT': Args['SBD_PORT']
            }, PluginInfo)
        else:
            OWTFLogger.log("Reusing initial connection..")
        Content += ServiceLocator.get_component("interactive_shell").run(
            Args['COMMAND_PREFIX'] + Args['TEST'] + Args['COMMAND_SUFFIX'], PluginInfo)
        OWTFLogger.log("Sleeping " + DELAY_BETWEEN_COMMANDS + " second(s) (increases reliability)..")
        time.sleep(int(DELAY_BETWEEN_COMMANDS))
        if not REUSE_CONNECTION:
            ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
        Iteration += 1  # Increase Iteration counter
    if not ServiceLocator.get_component("interactive_shell").IsClosed():  # Ensure clean exit if reusing connection
        ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
    return Content
