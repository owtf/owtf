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

Cross Site Flashing semi passive plugin: Tries to retrieve the crossdomain.xml
file and display it for review
"""
import re
import cgi
import logging
from framework.utils import OWTFLogger
from framework.dependency_management.dependency_resolver import ServiceLocator
DESCRIPTION = "Normal requests for XSF analysis"


def run(PluginInfo):
    URLList = []
    for File in ["crossdomain.xml", "clientaccesspolicy.xml"]:
        for URL in ServiceLocator.get_component("target").GetAsList(['target_url', 'top_url']):
            URLList.append(URL+"/"+File)  # Compute all URL + File combinations
    # The requester framework component will unique the URLs
    TransactionList = ServiceLocator.get_component("requester").GetTransactions(True, URLList)
    # Even though we have transaction list, those transactions do not have id
    # because our proxy stores the transactions and not the requester. So the
    # best way is to use the url list to retrieve transactions while making the
    # report
    return(ServiceLocator.get_component("plugin_helper").TransactionTableForURLList(True, URLList))
