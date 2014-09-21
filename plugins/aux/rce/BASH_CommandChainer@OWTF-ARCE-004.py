from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator

"""
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
import time
import logging

DESCRIPTION = "Runs a chain of commands on an agent server via SBD -i.e. for IDS testing-"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = DESCRIPTION + " Results:<br />"
    Iteration = 1  # Iteration counter initialisation
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    for Args in plugin_params.GetArgs({
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
                                                                          'ISHELL_REUSE_CONNECTION': config.Get(
                                                                                  'ISHELL_REUSE_CONNECTION_DESCRIP'),
                                                                          'ISHELL_EXIT_METHOD': config.Get(
                                                                                  'ISHELL_EXIT_METHOD_DESCRIP'),
                                                                          'ISHELL_DELAY_BETWEEN_COMMANDS': config.Get(
                                                                                  'ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
                                                                          'ISHELL_COMMANDS_BEFORE_EXIT': config.Get(
                                                                                  'ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
                                                                          'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.Get(
                                                                                  'ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
                                                                          'REPEAT_DELIM': config.Get('REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)  # Sets the aux plugin arguments as config
        REUSE_CONNECTION = (Args['ISHELL_REUSE_CONNECTION'] == 'yes')
        #print "REUSE_CONNECTION=" + str(REUSE_CONNECTION)
        DELAY_BETWEEN_COMMANDS = Args['ISHELL_DELAY_BETWEEN_COMMANDS']
        #print "Args="+str(Args)
        #print "'ISHELL_COMMANDS_BEFORE_EXIT_DELIM'=" + Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM']
        #break
        if Iteration == 1 or not REUSE_CONNECTION:
            ServiceLocator.get_component("interactive_shell").Open({
                                                                   'ConnectVia': config.GetResources('RCE_SBD_Connection')
                                                                   , 'InitialCommands': None
                                                                   #[ Args['BROWSER_PATH'] + ' about:blank']
                                                                   , 'ExitMethod': Args['ISHELL_EXIT_METHOD']
                                                                   , 'CommandsBeforeExit': Args[
                'ISHELL_COMMANDS_BEFORE_EXIT']
                                                                   , 'CommandsBeforeExitDelim': Args[
                'ISHELL_COMMANDS_BEFORE_EXIT_DELIM']
                                                                   , 'RHOST': Args['RHOST']
                                                                   , 'RPORT': Args['SBD_PORT']
                                                                   }, PluginInfo)
        else:
            OWTFLogger.log("Reusing initial connection..")
        ServiceLocator.get_component("interactive_shell").Run(
            Args['COMMAND_PREFIX'] + Args['TEST'] + Args['COMMAND_SUFIX'])
        OWTFLogger.log("Sleeping " + DELAY_BETWEEN_COMMANDS + " second(s) (increases reliability)..")
        time.sleep(int(DELAY_BETWEEN_COMMANDS))
        if not REUSE_CONNECTION:
            ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
        #Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', ServiceLocator.get_component("config").GetResources('LaunchExploit_'+Args['CATEGORY']+"_"+Args['SUBCATEGORY']), PluginInfo, "") # No previous output
        Iteration += 1  # Increase Iteration counter
    if not ServiceLocator.get_component("interactive_shell").IsClosed():  # Ensure clean exit if reusing connection
        ServiceLocator.get_component("interactive_shell").Close(PluginInfo)
    return Content