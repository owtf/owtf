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

GREP Plugin for Credentials transport over an encrypted channel (OWASP-AT-001)
https://www.owasp.org/index.php/Testing_for_credentials_transport_%28OWASP-AT-001%29
NOTE: GREP plugins do NOT send traffic to the target and only grep the HTTP Transaction Log
"""
import logging
DESCRIPTION = "Searches transaction DB for credentials protections"

def run(Core, PluginInfo):
	#Core.Config.Show()
        # TODO: Needs fixing
        """
	Content = "This plugin looks for password fields and then checks the URL (i.e. http vs. https)<br />"
	Content += "Uniqueness in this case is performed via URL + password field"
	# This retrieves all hidden password fields found in the DB response bodies:
	Command, RegexpName, Matches = Core.DB.Transaction.GrepMultiLineResponseRegexp(Core.Config.Get('RESPONSE_REGEXP_FOR_PASSWORDS'))
	# Now we need to check if the URL is https or not and count the insecure ones (i.e. not https)
	IDs = []
	InsecureMatches = []
	for ID, FileMatch in Matches:
		if ID not in IDs: # Retrieve Transaction from DB only once
			IDs.append(ID) # Process each transaction only once
			Transaction = Core.DB.Transaction.GetByID(ID)
		if 'https' != Transaction.URL.split(":")[0]:
			Core.log("Transaction: "+ID+" contains passwords fields with a URL different than https")
			InsecureMatches.append([ID, Transaction.URL+": "+FileMatch]) # Need to make the unique work by URL + password
	Message = "<br /><u>Total insecure matches: "+str(len(InsecureMatches))+'</u>'
	Core.log(Message)
	Content += Message+"<br />"
	Content += Core.PluginHelper.DrawResponseMatchesTables([Command, RegexpName, InsecureMatches], PluginInfo)
	return Content
        """
        return []
