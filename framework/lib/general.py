#!/usr/bin/env python
"""
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org                                                        
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
                                                                                                           

This library contains helper functions and exceptions for the framework
"""
import pprint, sys
from collections import defaultdict

class FrameworkException(Exception):
    def __init__(self, value):
	    self.parameter = value

    def __str__(self):
	    return repr(self.parameter)

class FrameworkAbortException(FrameworkException):
	pass

class PluginAbortException(FrameworkException):
	pass

class UnreachableTargetException(FrameworkException):
	pass

def ConfigGet(Key): # Kludge wrapper function
	global Config # kludge global to avoid having to pass the config around to other components that need it (temporary until I figure out a better way!)
        return Config.Get(Key)

def cprint(Message):
        Pad = "[*] "
        print Pad+str(Message).replace("\n", "\n"+Pad)
        return Message

def p(Variable):
	cprint("depth = 1")
	pprint.PrettyPrinter(indent=4,depth=1).pprint(Variable)
	cprint("depth = 2")
	pprint.PrettyPrinter(indent=4,depth=2).pprint(Variable)
	cprint("pprint")
        pprint.pprint(Variable)
	cprint("print dir")
        cprint(dir(Variable))

# Perform multiple replacements in one go using the replace dictionary in format: { 'search' : 'replace' }
def MultipleReplace(Text, ReplaceDict):
        NewText = Text
        for Search,Replace in ReplaceDict.items():
                NewText = NewText.replace(Search, str(Replace))
        return NewText

def WipeBadCharsForFilename(Filename):
        return MultipleReplace(Filename, { '(':'', ' ':'_', ')':'', '/':'_' })

def RemoveListBlanks(List):
	NewList = []
	for Item in List:
		if Item:
			NewList.append(Item)
	return NewList

def List2DictKeys(List):
	Dictionary = defaultdict(list)
	for Item in List:
		Dictionary[Item] = ''
	return Dictionary

def AddToDict(FromDict, ToDict):
	for Key, Value in FromDict.items():
		if hasattr(Value, 'copy') and callable(getattr(Value, 'copy')):
			ToDict[Key] = Value.copy()
		else:
			ToDict[Key] = Value

def MergeDicts(Dict1, Dict2): # Returns a by-value copy contained the merged content of the 2 passed dictionaries
	NewDict = defaultdict(list)
	AddToDict(Dict1, NewDict)
	AddToDict(Dict2, NewDict)
	return NewDict
		 
def TruncLines(Str, NumLines, EOL = "\n"):
	return EOL.join(Str.split(EOL)[0:NumLines])

def DeriveHTTPMethod(Method, Data): # Derives the HTTP method from Data, etc
	DMethod = Method
        if DMethod == None or DMethod == '': # Method not provided: Determine method from params
        	DMethod = 'GET'
                if Data != '' and Data != None:
                	DMethod = 'POST'
	return DMethod

def GetDictValueOrBlank(Dict, Key): # Return the value if the key is present or blank otherwise
	if Key in Dict:
		return Dict[Key]
	return ''

def CallMethod(Object, Method, ArgList): # Calls Object.Method(ArgList) dynamically, this helps avoiding code repetition via wrapper convenience functions
	return getattr(Object, Method)(*ArgList)

def GetUnique(List):
	NewList = []
	for Item in List:
		if Item not in NewList:
			NewList.append(Item)
	return NewList

def GetFileAsList(Filename):
	try:
		Output = open(Filename, 'r').read().split("\n")
		cprint("Loaded file: '"+Filename+"'")
	except IOError, error:
		cprint("Cannot open file: '"+Filename+"' ("+str(sys.exc_info())+")")
		Output = []
	return Output

