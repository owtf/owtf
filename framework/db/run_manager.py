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

The DB stores HTTP transactions, unique URLs and more. 
'''
# Run DB field order:
# Start, End, Runtime, Command, LogStatus = self.Core.DB.DBCache['RUN_DB'][-1]#.split(" | ")
RSTART = 0
REND = 1
RRUNTIME = 2
RCOMMAND = 3
RSTATUS = 4

class RunManager:
	def __init__(self, Core):
		self.Core = Core

	def StartRun(self, Command):
		Start, Time = self.Core.Timer.StartTimer('owtf')
		Runtime = End = "?"
		Status = "Running"
		#self.Core.DB.DBCache['RUN_DB'].append([ Start, End, Runtime, Command, Status ])
		self.Core.DB.Add('RUN_DB', [ Start, End, Runtime, Command, Status ] )

	def EndRun(self, Status = 'Complete'): # Modify last run info
		LastRecord = self.Core.DB.GetRecord('RUN_DB', -1)
		LastRecord[REND] = self.Core.Timer.GetCurrentDateTime()
		LastRecord[RRUNTIME] = self.Core.Timer.GetElapsedTimeAsStr('owtf')
		LastRecord[RSTATUS] = Status
		self.Core.DB.ModifyRecord('RUN_DB', -1, LastRecord)
		#self.Core.DB.DBCache['RUN_DB'][-1][REND] = self.Core.Timer.GetCurrentDateTime()
		#self.Core.DB.DBCache['RUN_DB'][-1][RRUNTIME] = self.Core.Timer.GetElapsedTimeAsStr('owtf')
		#self.Core.DB.DBCache['RUN_DB'][-1][RSTATUS] = Status

