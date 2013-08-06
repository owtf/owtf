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

This plugin does not perform ANY test: The aim is to visit all URLs grabbed so far and build the transaction log to feed data to other plugins
NOTE: This is an active plugin because it may visit URLs retrieved by vulnerability scanner spiders which may be considered sensitive or include vulnerability probing
"""
import logging

DESCRIPTION = "Visit URLs found by other tools, some could be sensitive: need permission"

def run(Core, PluginInfo):
	#Core.Config.Show()
	crap = { 'test' : '1', 'test2' : '2' }
	Log("Crap="+str(crap))
	return 'test'
	Count = 0
	Core.DB.URL.AddURLsStart() # Keep cocunt of URLs
	for URL in Core.DB.URL.GetURLsToVisit(Core.DB.GetData('POTENTIAL_ALL_URLS_DB')):
		if not Core.DB.Transaction.IsTransactionAlreadyAdded(URL): # Count only new URLs, not in the cache
			Count += 1 # TODO: Check
		Core.Requester.GetTransaction(True, URL) # Use cache if possible
	Core.DB.URL.AddURLsEnd()
	Content = str(Count)+" URLs were visited"
	Log(Content)
	return Content

