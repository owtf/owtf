#!/usr/bin/env python
'''
This is the command-line front-end in charge of processing arguments and call the framework
'''

import getopt
import sys
import os
import subprocess
from collections import defaultdict


def GetName():
    return sys.argv[0]


def Usage(Message):
    print "Usage:"
    print "%s EMAIL_TARGET=? EMAIL_FROM=? SMTP_LOGIN=? SMTP_PASS=? " \
        "SMTP_HOST=? SMTP_PORT=? EMAIL_PRIORITY=? PDF_TEMPLATE=? MSF_LISTENER_PORT=? " \
        "MSF_LISTENER_SETUP=? ATTACHMENT_NAME=? SET_EMAIL_TEMPLATE=? PHISHING_PAYLOAD=? " \
        "PHISHING_SCRIPT_DIR=? TOOL_SET_DIR=?" % (GetName())
    print "ERROR: %s" % Message
    sys.exit(-1)


def ShellExec(Command):
    print "\nExecuting (Control+C to abort THIS COMMAND ONLY):\n%s" % Command
    Output = ''
    # noqa Stolen from: http://stackoverflow.com/questions/5833716/how-to-capture-output-of-a-shell-script-running-in-a-separate-process-in-a-wxpyt
    try:
        proc = subprocess.Popen(Command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print MultipleReplace(line, {"\n": "", "\r": ""})  # Show progress on the screen too!
            Output += line  # Save as much output as possible before a tool crashes! :)
    except KeyboardInterrupt:
        Output += self.Core.Error.UserAbort('Command', Output)  # Identify as Command Level abort
    return Output


# Perform multiple replacements in one go using the replace dictionary in format: { 'search' : 'replace' }
def MultipleReplace(Text, ReplaceDict):
    NewText = Text
    for Search, Replace in ReplaceDict.items():
        NewText = NewText.replace(Search, str(Replace))
    return NewText


def GetParams():  # Basic validation and parameter retrieval:
    MandatoryParams = ['EMAIL_TARGET', 'EMAIL_FROM', 'SMTP_LOGIN', 'SMTP_PASS',
                       'SMTP_HOST', 'SMTP_PORT', 'EMAIL_PRIORITY', 'PDF_TEMPLATE', 'MSF_LISTENER_PORT',
                       'MSF_LISTENER_SETUP', 'ATTACHMENT_NAME', 'SET_EMAIL_TEMPLATE', 'PHISHING_PAYLOAD',
                       'PHISHING_SCRIPT_DIR', 'TOOL_SET_DIR']

    ScriptName = GetName()
    try:
        Opts, Args = getopt.getopt(sys.argv[1:], "a:")
    except getopt.GetoptError:
        Usage("Invalid %s option(s)" % ScriptName)

    Params = defaultdict(list)
    for Arg in Args:
        Chunks = Arg.split('=')
        if len(Chunks) != 2:
            Usage("'%s' is incorrect: The parameter format is ARGNAME=ARGVALUE" % str(Arg))
        ArgName = Chunks[0]
        ArgValue = Arg.replace(ArgName+"=", '')
        Params[ArgName] = ArgValue

    for Mandatory in MandatoryParams:
        if Mandatory not in Params:
            Usage("Must include parameter: %s" % Mandatory)

    SETScript = "%s/set_scripts/payload%s.set" % (Params['PHISHING_SCRIPT_DIR'], Params['PHISHING_PAYLOAD'])
    SETDebugAutomate = "%s/set_debug_automate.sh" % Params['PHISHING_SCRIPT_DIR']
    MandatoryPaths = [Params['TOOL_SET_DIR'], Params['PDF_TEMPLATE'],
                      Params['EMAIL_TARGET'], SETScript, SETDebugAutomate]
    for Path in MandatoryPaths:
        if not os.path.exists(Path):
            Usage("The path '%s' must exist in your filesystem" % str(Path))
    Params['SET_PARAMS_SCRIPT'] = SETScript
    Params['SET_TMP_SCRIPT'] = "/tmp/set_tmp_script.set"
    Params['SET_DEBUG_AUTOMATE'] = SETDebugAutomate
    return Params

# Step 1 - Retrieve params and basic validation
Params = GetParams()
# Step 2 - Create temporary script with hard-coded values from parameters:
with open(Params['SET_TMP_SCRIPT'], 'w') as file:
    file.write(MultipleReplace(open(Params['SET_PARAMS_SCRIPT']).read(), Params))

# Step 3 - Run SET script
ShellExec("%s %s %s" % (Params['SET_DEBUG_AUTOMATE'], Params['TOOL_SET_DIR'], Params['SET_TMP_SCRIPT']))

# Step 4 - Remove temporary script with hard-coded values
ShellExec("rm -f %s" % Params['SET_TMP_SCRIPT'])
