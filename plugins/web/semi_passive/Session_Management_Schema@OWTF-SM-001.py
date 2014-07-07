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

SEMI-PASSIVE Plugin for Testing for Session Management Schema (OWASP-SM-001)
https://www.owasp.org/index.php/Testing_for_Session_Management_Schema_%28OWASP-SM-001%29
"""

import string, re
import cgi,logging
from framework.lib import general

DESCRIPTION = "Normal requests to gather session managament info"

def run(Core, PluginInfo):
        #Core.Config.Show()
        # True = Use Transaction Cache if possible: Visit the start URLs if not already visited
        # Step 1 - Find transactions that set cookies
        # Step 2 - Request 10 times per URL that sets cookies
        # Step 3 - Compare values and calculate randomness
        URLList = []
        TransactionList = []
        Result = ""
        return([])
        # TODO: Try to keep up Abe's promise ;)
        #return "Some refactoring required, maybe for BSides Vienna 2012 but no promises :)"
        for ID in Core.DB.Transaction.GrepTransactionIDsForHeaders([Core.Config.Get('HEADERS_FOR_COOKIES')]):# Transactions with cookies
                URL = Core.DB.Transaction.GetByID(ID).URL # Limitation: Not Checking POST, normally not a problem ..
                if URL not in URLList: # Only if URL not already processed!
                        URLList.append(URL) # Keep track of processed URLs
                        AllCookieValues = {}
                        for i in range(0,2): # Get more cookies to perform analysis
                                Transaction = Core.Requester.GetTransaction(False, URL)
        return Result
