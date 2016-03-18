#!/usr/bin/env python
'''
This is the command-line front-end in charge of processing arguments and call the framework
'''
import getopt, sys, os
import subprocess
from collections import defaultdict

def GetName():
	return sys.argv[0]

def Usage(Message):
	print "Usage:"
	print GetName()+" EMAIL_TARGET=? EMAIL_FROM=? SMTP_LOGIN=? SMTP_PASS=? SMTP_HOST=? SMTP_PORT=? EMAIL_PRIORITY=? PDF_TEMPLATE=? MSF_LISTENER_PORT=? MSF_LISTENER_SETUP=? ATTACHMENT_NAME=? SET_EMAIL_TEMPLATE=? PHISHING_PAYLOAD=? PHISHING_SCRIPT_DIR=? TOOL_SET_DIR=?"
	print "ERROR: "+Message
	sys.exit(-1)

def ShellExec(Command):
	print "\nExecuting (Control+C to abort THIS COMMAND ONLY):\n"+Command
	Output = ''
	try: # Stolen from: http://stackoverflow.com/questions/5833716/how-to-capture-output-of-a-shell-script-running-in-a-separate-process-in-a-wxpyt
		proc = subprocess.Popen(Command, shell=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			bufsize=1)
		while True:
			line = proc.stdout.readline()
			if not line: break
			print MultipleReplace(line, { "\n":"", "\r":"" }) # Show progress on the screen too!
			Output += line # Save as much output as possible before a tool crashes! :)
	except KeyboardInterrupt:
		Output += self.Core.Error.UserAbort('Command', Output) # Identify as Command Level abort
	return Output

# Perform multiple replacements in one go using the replace dictionary in format: { 'search' : 'replace' }
def MultipleReplace(Text, ReplaceDict):
	NewText = Text
	for Search,Replace in ReplaceDict.items():
		NewText = NewText.replace(Search, str(Replace))
	return NewText

def GetParams(): # Basic validation and parameter retrieval:
	MandatoryParams = [ 'EMAIL_TARGET', 'EMAIL_FROM', 'SMTP_LOGIN', 'SMTP_PASS', 'SMTP_HOST', 'SMTP_PORT', 'EMAIL_PRIORITY', 'PDF_TEMPLATE', 'MSF_LISTENER_PORT', 'MSF_LISTENER_SETUP', 'ATTACHMENT_NAME', 'SET_EMAIL_TEMPLATE', 'PHISHING_PAYLOAD', 'PHISHING_SCRIPT_DIR', 'TOOL_SET_DIR' ]

	ScriptName = GetName()
	try:
		Opts, Args = getopt.getopt(sys.argv[1:],"a:") 
	except getopt.GetoptError:
		Usage("Invalid "+ScriptName+" option(s)")

	Params = defaultdict(list)
	for Arg in Args:
		Chunks = Arg.split('=')
		if len(Chunks) != 2:
			Usage("'"+str(Arg)+"' is incorrect: The parameter format is ARGNAME=ARGVALUE")
		ArgName = Chunks[0]
		ArgValue = Arg.replace(ArgName+"=", '')
		Params[ArgName] = ArgValue

	for Mandatory in MandatoryParams:
		if Mandatory not in Params:
			Usage("Must include parameter: "+Mandatory)

	SETScript = Params['PHISHING_SCRIPT_DIR']+"/set_scripts/payload"+Params['PHISHING_PAYLOAD']+".set"
	SETDebugAutomate = Params['PHISHING_SCRIPT_DIR']+"/set_debug_automate.sh"
	MandatoryPaths = [ Params['TOOL_SET_DIR'], Params['PDF_TEMPLATE'], Params['EMAIL_TARGET'], SETScript, SETDebugAutomate ]
	for Path in MandatoryPaths:
		if not os.path.exists(Path):
			Usage("The path '"+str(Path)+"' must exist in your filesystem")
	Params['SET_PARAMS_SCRIPT'] = SETScript
	Params['SET_TMP_SCRIPT'] = "/tmp/set_tmp_script.set"
	Params['SET_DEBUG_AUTOMATE'] = SETDebugAutomate
	return Params

Params = GetParams() # Step 1 - Retrieve params and basic validation
with open(Params['SET_TMP_SCRIPT'], 'w') as file: # Step 2 - Create temporary script with hard-coded values from parameters:
	file.write(MultipleReplace(open(Params['SET_PARAMS_SCRIPT']).read(), Params))

ShellExec(Params['SET_DEBUG_AUTOMATE']+" "+Params['TOOL_SET_DIR']+" "+Params['SET_TMP_SCRIPT']) # Step 3 - Run SET script
ShellExec("rm -f "+Params['SET_TMP_SCRIPT']) # Step 4 - Remove temporary script with hard-coded values
