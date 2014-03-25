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

Component to handle data storage and search of all commands run
'''

from framework.lib.general import *
# Run DB field order:
# Start, End, Runtime, Command, LogStatus = self.Core.DB.DBCache['RUN_DB'][-1]#.split(" | ")
START = 0
END = 1
RUNTIME = 2 
STATUS = 3 
TARGET = 4 # The same plugin and type can be run against different targets, they should have different paths, but we need the target to get the right codes in the report
MODIFIED_COMMAND = 5 
ORIGINAL_COMMAND = 6 

NAME_TO_OFFSET = { 'Start' : START, 'End' : END, 'RunTime' : RUNTIME, 'Status' : STATUS, 'Target' : TARGET, 'ModifiedCommand' : MODIFIED_COMMAND, 'OriginalCommand' : ORIGINAL_COMMAND }

class CommandRegister(object):
	def __init__(self, Core):
		self.Core = Core

	def AlreadyRegistered(self, OriginalCommand): # Need to ignore plugin output dirs, etc. Hence "OriginalCommand", otherwise the same command would be different!
		Matches = self.Search( { 'OriginalCommand' : OriginalCommand.strip() } )
		if len(Matches) > 0:
			for Match in Matches:
				if Match['Status'] == 'Finished':
					return Match['Target'] # The command finished successfully
		return False # The command never finished

	def Add(self, Command): # Must always register a command when it is run, we do not care if it was run before for this
		#print "Command=" + str(Command)
		self.Core.DB.Add('COMMAND_REGISTER', [ Command['Start'], Command['End'], Command['RunTime'], Command['Status'], Command['Target'], Command['ModifiedCommand'].strip(), Command['OriginalCommand'].strip() ] )
		#if not self.AlreadyRegistered(Command['OriginalCommand']):

	def Search(self, Criteria):
		return self.Core.DB.Search('COMMAND_REGISTER', Criteria, NAME_TO_OFFSET)
