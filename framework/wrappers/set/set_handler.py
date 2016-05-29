#!/usr/bin/env python
'''
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
	def __init__(self):
		pexpect_shell.PExpectShell.__init__(self) # Calling parent class to do its init part
		self.CommandTimeOffset = 'SETCommand'
		self.SpearPhishing = spear_phishing.SpearPhishing(self)
		
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
"""
with open(Params['SET_TMP_SCRIPT'], 'w') as file: # Step 2 - Create temporary script with hard-coded values from parameters:
	file.write(MultipleReplace(open(Params['SET_PARAMS_SCRIPT']).read(), Params))

ShellExec(Params['SET_DEBUG_AUTOMATE']+" "+Params['TOOL_SET_DIR']+" "+Params['SET_TMP_SCRIPT']) # Step 3 - Run SET script
ShellExec("rm -f "+Params['SET_TMP_SCRIPT']) # Step 4 - Remove temporary script with hard-coded values
"""
