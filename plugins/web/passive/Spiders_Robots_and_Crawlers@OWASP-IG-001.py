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

"""
DESCRIPTION = "robots.txt analysis through third party sites"

def run(Core, PluginInfo):
	TestResult = ''
	Count = 1
	Content = Core.PluginHelper.RequestAndDrawLinkList('Passive Analysis Results', Core.Config.GetResources('PassiveRobotsAnalysisHTTPRequests'), PluginInfo)
	Content += Core.PluginHelper.DrawResourceLinkList('Online Resources', Core.Config.GetResources('PassiveRobotsAnalysisLinks'))
	for Name, Resource in Core.Config.GetResources('PassiveRobots'): # Try to retrieve the robots.txt file from all defined resources
		URL = Resource # Just for clarity
		LinkStart, LinkFinish = URL.split('/robots.txt') # Preparing link chunks for disallowed entries
		#print "URL="+URL+", PatternStart="+PatternStart+", PatternEnd="+PatternEnd+" LinkStart="+LinkStart+", LinkFinish="+LinkFinish
		LinkStart = LinkStart.strip()
		LinkFinish = LinkFinish.strip()
		TestResult += Core.Reporter.Render.DrawButtonLink(Name, URL)
		Transaction = Core.Requester.GetTransaction(True, URL) # Use the cache if possible for speed
		if Transaction.Found:
			TestResult += "<br /><br />Raw regexp processing:<br />"
			TestResult += Core.PluginHelper.ProcessRobots(PluginInfo, Transaction.GetRawResponseBody(), LinkStart, LinkFinish, 'robots'+str(Count)+'.txt')
			Count += 1
		else: # Not found or unknown request error
			Message = "could not be retrieved using resource: "+Resource
			print Message
			#TestResult += Message+".: \n"+cgi.escape(Transaction.GetRawResponse())
		TestResult += Core.Reporter.DrawHTTPTransactionTable([ Transaction ])
	return Content+TestResult
