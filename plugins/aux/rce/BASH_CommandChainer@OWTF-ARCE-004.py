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
def run(Core, PluginInfo):
	#Core.Config.Show()
	Content = DESCRIPTION + " Results:<br />"
	Iteration = 1 # Iteration counter initialisation
	for Args in Core.PluginParams.GetArgs( { 
'Description' : DESCRIPTION,
'Mandatory' : { 
		'RHOST' : Core.Config.Get('RHOST_DESCRIP'),
		'SBD_PORT' : Core.Config.Get('SBD_PORT_DESCRIP'),
		'SBD_PASSWORD' : Core.Config.Get('SBD_PASSWORD_DESCRIP'),
		'COMMAND_PREFIX' : 'The command string to be pre-pended to the tests (i.e. /usr/lib/firefox... http...)',
		}, 
'Optional' : {
		'TEST' : 'The test to be included between prefix and suffix',
		'COMMAND_SUFIX' : 'The URL to be appended to the tests (i.e. ...whatever)',
		'ISHELL_REUSE_CONNECTION' : Core.Config.Get('ISHELL_REUSE_CONNECTION_DESCRIP'),
		'ISHELL_EXIT_METHOD' : Core.Config.Get('ISHELL_EXIT_METHOD_DESCRIP'),
		'ISHELL_DELAY_BETWEEN_COMMANDS' : Core.Config.Get('ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
		'ISHELL_COMMANDS_BEFORE_EXIT' : Core.Config.Get('ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
		'ISHELL_COMMANDS_BEFORE_EXIT_DELIM' : Core.Config.Get('ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
		'REPEAT_DELIM' : Core.Config.Get('REPEAT_DELIM_DESCRIP')
		} }, PluginInfo):
		Core.PluginParams.SetConfig(Args) # Sets the aux plugin arguments as config
		REUSE_CONNECTION = (Args['ISHELL_REUSE_CONNECTION'] == 'yes')
		#print "REUSE_CONNECTION=" + str(REUSE_CONNECTION)
		DELAY_BETWEEN_COMMANDS = Args['ISHELL_DELAY_BETWEEN_COMMANDS']
		#print "Args="+str(Args)
		#print "'ISHELL_COMMANDS_BEFORE_EXIT_DELIM'=" + Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM']
		#break
		if Iteration == 1 or not REUSE_CONNECTION:
			Core.InteractiveShell.Open({
				'ConnectVia' : Core.Config.GetResources('RCE_SBD_Connection')
				, 'InitialCommands' : None #[ Args['BROWSER_PATH'] + ' about:blank']
				, 'ExitMethod' : Args['ISHELL_EXIT_METHOD']
				, 'CommandsBeforeExit' : Args['ISHELL_COMMANDS_BEFORE_EXIT']
				, 'CommandsBeforeExitDelim' : Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM']
				, 'RHOST' : Args['RHOST']
				, 'RPORT' : Args['SBD_PORT']
							  }, PluginInfo)
		else:
			Core.log("Reusing initial connection..")
		Core.InteractiveShell.Run(Args['COMMAND_PREFIX']+Args['TEST']+Args['COMMAND_SUFIX'])
		Core.log("Sleeping " + DELAY_BETWEEN_COMMANDS + " second(s) (increases reliability)..")
		time.sleep(int(DELAY_BETWEEN_COMMANDS))
		#Core.RemoteShell.Run("sleep " + str(WAIT_SECONDS))
		if not REUSE_CONNECTION:
			Core.InteractiveShell.Close(PluginInfo)
		#Content += Core.PluginHelper.DrawCommandDump('Test Command', 'Output', Core.Config.GetResources('LaunchExploit_'+Args['CATEGORY']+"_"+Args['SUBCATEGORY']), PluginInfo, "") # No previous output
		Iteration += 1 # Increase Iteration counter
	if not Core.InteractiveShell.IsClosed(): # Ensure clean exit if reusing connection
		Core.InteractiveShell.Close(PluginInfo)
	return Content