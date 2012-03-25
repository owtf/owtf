#!/usr/bin/env python
'''
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

Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome the limitations of set-automate
'''
from framework.lib.general import *
import time

SCRIPT_DELAY=2
class SpearPhishing:
	def __init__(self, Core):
		self.Core = Core
		
	def Run(self, Args, PluginInfo):
		Output = ''
		if self.Init(Args):
			self.Core.SET.Open({
						'ConnectVia' : self.Core.Config.GetResources('OpenSET')
						, 'InitialCommands' : None
						, 'ExitMethod' : Args['ISHELL_EXIT_METHOD']
						, 'CommandsBeforeExit' : Args['ISHELL_COMMANDS_BEFORE_EXIT']
						, 'CommandsBeforeExitDelim' : Args['ISHELL_COMMANDS_BEFORE_EXIT_DELIM']
								}, PluginInfo)
			if Args['PHISHING_CUSTOM_EXE_PAYLOAD_DIR']: # Prepend directory to payload
				Args['PHISHING_CUSTOM_EXE_PAYLOAD'] = Args['PHISHING_CUSTOM_EXE_PAYLOAD_DIR'] + "/" + Args['PHISHING_CUSTOM_EXE_PAYLOAD']
			for Script in self.GetSETScripts(Args):
				cprint("Running SET script: " + Script)
				Output += self.Core.SET.RunScript(Script, Args, Debug=False)
				cprint("Sleeping " + str(SCRIPT_DELAY) + " seconds..")
				time.sleep(int(SCRIPT_DELAY))
				#Output += self.Core.SET.RunScript(self.SETScript, Args, Debug=False)
			self.Core.SET.Close(PluginInfo)
		return Output
	
	def GetSETScripts(self, Args):
		return [
					Args['PHISHING_SCRIPT_DIR']+"/start_phishing.set"
					, Args['PHISHING_SCRIPT_DIR']+"/payload_"+Args['PHISHING_PAYLOAD']+".set"
					, Args['PHISHING_SCRIPT_DIR']+"/send_email_smtp.set"
				]
	
	def InitPaths(self, Args):
		MandatoryPaths = self.Core.Config.GetAsList( [ 'TOOL_SET_DIR', '_PDF_TEMPLATE', '_EMAIL_TARGET' ] )
		if not PathsExist(MandatoryPaths):
			self.Core.Error.FrameworkAbort("USER ERROR: Some mandatory paths were not found your filesystem", 'user')
			return False
		return True
	
	def Init(self, Args):
		if not self.InitPaths(Args):
			return False
		return True