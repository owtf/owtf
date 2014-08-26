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

Robots.txt semi-passive plugin, parses robots.txt file to generate on-screen
links and save them for later spidering and analysis
"""
import re
import cgi
import logging

DESCRIPTION = "Normal request for robots.txt analysis"


def run(Core, PluginInfo):
    TopURL = Core.DB.Target.Get('TOP_URL')
    URL = TopURL+"/robots.txt"
    TestResult = []
    # Use transaction cache if possible for speed
    HTTP_Transaction = Core.Requester.GetTransaction(True, URL)
    if HTTP_Transaction.Found:
        TestResult += Core.PluginHelper.ProcessRobots(
            PluginInfo,
            HTTP_Transaction.GetRawResponseBody(),
            TopURL,
            '')
    else:  # robots.txt NOT found
        Core.log("robots.txt was NOT found")
        TestResult += Core.PluginHelper.TransactionTableForURLList(True, [URL])
    return TestResult
