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

The health-check module verifies the integrity of the configuration, mainly checking that tool paths exist
'''
import os
from framework.lib.general import *

class HealthCheck:
	def __init__(self, Core):
		self.Core = Core

	def Run(self):
		Count = 0
		for Key, Value in self.Core.Config.GetConfig()['string'].items():
			Setting = self.Core.Config.StripKey(Key)
			if Setting.startswith('TOOL_') and not os.path.exists(Value):
				cprint("WARNING: Tool path not found for: "+str(Value))
				Count += 1
		self.ShowHelp(Count)

	def ShowHelp(self, Count):
		if Count > 0:
			cprint("")
			cprint("WARNING!!!: "+str(Count)+" tools could not be found. Some suggestions:")
			cprint(" - Define where your tools are here: "+str(self.Core.Config.Profiles['g']))
			cprint(" - Use the "+self.Core.Config.RootDir+"/tools/bt5_install.sh script to install missing tools")
			if self.Core.Config.Get('INTERACTIVE') and 'n' == raw_input("Continue anyway? [y/n]"):
				self.Core.Error.FrameworkAbort("Aborted by user")
		else:
			cprint("SUCCESS: Integrity Check successful -> All tools were found")
