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
from collections import defaultdict
from framework.lib.general import *
from framework.shell import pexpect_shell
from framework.wrappers.set import spear_phishing
import time
import pexpect

class SETHandler(pexpect_shell.PExpectShell):
	def __init__(self, Core):
		pexpect_shell.PExpectShell.__init__(self, Core) # Calling parent class to do its init part
		self.CommandTimeOffset = 'SETCommand'
		self.SpearPhishing = spear_phishing.SpearPhishing(Core)
		
	def RunScript(self, ScriptPath, Args, Debug = False):
		#TODO: Replacements
		Output = ""
		for Step in MultipleReplace(open(ScriptPath).read(), Args).split("\n"):
			#Output += self.Read(5)
			#print "self.CommandInfo=" + str(self.CommandInfo)
			#p(self.CommandInfo)
			if not Step.strip(): 
				cprint("WARNING: Sending Blank!") #Necessary sometimes, but warn
			if Debug:
				print "Step: " + str(Step)
			else:
				Output += self.Run(Step)
				if Step == 'exit':
					self.Kill()
				#print str(self.Connection.before) + str(self.Connection.after)
				#print "Before=" + str(self.Connection.before)
				#print "After=" + str(self.Connection.after)
				cprint("Waiting " + Args['ISHELL_DELAY_BETWEEN_COMMANDS'] + " seconds for SET to process step.. - " + Step)
				time.sleep(int(Args['ISHELL_DELAY_BETWEEN_COMMANDS']))
				self.Expect('set.*>|Password for open-relay', TimeOut = 120)
				#self.Expect(pexpect.EOF)
				#Output += self.Read(5)
		return Output
			#print "Testing line=" + line 
		#self.RunCommandList(self.Core.GetFileAsList(FilePath))
"""
with open(Params['SET_TMP_SCRIPT'], 'w') as file: # Step 2 - Create temporary script with hard-coded values from parameters:
	file.write(MultipleReplace(open(Params['SET_PARAMS_SCRIPT']).read(), Params))

ShellExec(Params['SET_DEBUG_AUTOMATE']+" "+Params['TOOL_SET_DIR']+" "+Params['SET_TMP_SCRIPT']) # Step 3 - Run SET script
ShellExec("rm -f "+Params['SET_TMP_SCRIPT']) # Step 4 - Remove temporary script with hard-coded values
"""