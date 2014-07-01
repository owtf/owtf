#!/usr/bin/env python
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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

HTTP_Transaction is a container of useful HTTP Transaction information to
simplify code both in the framework and the plugins.

"""

import cgi
import logging

from httplib import responses as response_messages

from framework import timer
from framework.http.cookies import cookie_factory
from framework.lib.general import *


class HTTP_Transaction(object):
    def __init__(self, Timer):
        self.Timer = Timer
        self.New = False
        # If None, then get method will result in an error ;)
        self.GrepOutput = {}

    def ScopeToStr(self):
        return str(self.IsInScope)[0]

    def InScope(self):
        return(self.IsInScope)

    def Start(self, URL, Data, Method, IsInScope):
        self.IsInScope = IsInScope
        self.StartRequest()
        self.URL = URL
        self.InitData(Data)
        self.Method = DeriveHTTPMethod(Method, Data)
        self.Found = None
        self.RawRequest = ''
        self.ResponseHeaders = []
        self.Status = ''
        self.ID = ''
        self.HTMLLinkToID = ''
        self.New = True  # Flag new transaction.

    def InitData(self, Data):
        self.Data = Data
        if self.Data is None:
            # This simplifies other code later, no need to cast to str if None,
            # etc.
            self.Data = ''

    def StartRequest(self):
        self.Timer.StartTimer('Request')
        self.Time = self.TimeHuman = ''

    def EndRequest(self):
        self.Time = str(self.Timer.GetElapsedTime('Request'))
        self.TimeHuman = self.Timer.GetTimeAsStr(self.Time)

    def SetTransaction(self, Found, Request, Response):
        # Response can be "Response" for 200 OK or "Error" for everything else,
        # we don't care here.
        if self.URL != Response.url:
            if Response.code not in [302, 301]:  # No way, error in hook.
                # Mark as a redirect, dirty but more accurate than 200 :P
                self.Status = str(302) + " Found"
                self.Status += " --Redirect--> " + str(Response.code) + " "
                self.Status += Response.msg
            # Redirect differs in schema (i.e. https instead of http).
            if self.URL.split(':')[0] != Response.url.split(':')[0]:
                pass
                #self.IsInScope = False --> Breaks links, to be fixed in some next release
            self.URL = Response.url
        else:
            self.Status = str(Response.code) + " " + Response.msg
        self.RawRequest = Request
        self.Found = Found
        self.ResponseHeaders = Response.headers
        #p(self.ResponseHeaders)
        self.ResponseContents = Response.read()
        self.EndRequest()

    def SetTransactionFromDB(self,
                             id,
                             url,
                             method,
                             status,
                             time,
                             time_human,
                             request_data,
                             raw_request,
                             response_headers,
                             response_body,
                             grep_output):
        self.ID = id
        self.New = False  # Flag NOT new transaction.
        self.URL = url
        self.Method = method
        self.Status = status
        self.Found = (self.Status == "200 OK")
        self.Time = time
        self.TimeHuman = time_human
        self.Data = request_data
        self.RawRequest = raw_request
        #self.ResponseHeaders = ResponseHeaders.split("\n")
        self.ResponseHeaders = response_headers
        self.ResponseContents = response_body
        self.GrepOutput = grep_output
        cookies_list = []
        for header in self.ResponseHeaders.split('\n'):
            if header.split(':',1)[0].strip() == "Set-Cookie":
                cookies_list.append(header.split(':',1)[-1].strip())
        self.CookieString = ','.join(cookies_list)

    def GetGrepOutput(self):
        return (self.GrepOutput)

    def GetGrepOutputFor(self, regex_name):
        # Highly misleading name as grepping is already done when adding the
        # transaction.
        # To prevent python from going crazy when a key is missing.
        return (self.GrepOutput.get(regex_name, None))

    def SetError(self, ErrorMessage):
        # Only called for unknown errors, 404 and other HTTP stuff handled on
        # self.SetResponse.
        self.ResponseContents = ErrorMessage
        self.EndRequest()

    def GetID(self):
        return (self.ID)

    def SetID(self, ID, HTMLLinkToID):
        self.ID = ID
        self.HTMLLinkToID = HTMLLinkToID
        # Only for new transactions, not when retrieved from DB, etc.
        if self.New:
            log = logging.getLogger('general')
            log.info(
                "New owtf HTTP Transaction: " +
                " - ".join([
                    self.ID,
                    self.TimeHuman,
                    self.Status,
                    self.Method,
                    self.URL])
                )

    def GetHTMLLink(self, LinkName = ''):
        if '' == LinkName:
            LinkName = "Transaction " + self.ID
        return self.HTMLLinkToID.replace('@@@PLACE_HOLDER@@@', LinkName)

    def GetHTMLLinkWithTime(self, LinkName=''):
        return self.GetHTMLLink(LinkName) + " (" + self.TimeHuman + ")"

    def GetRawEscaped(self):
        return "<pre>" + cgi.escape(self.GetRaw()) +"</pre>"

    def GetRaw(self):
        return self.GetRawRequest() + "\n\n" + self.GetRawResponse()

    def GetRawRequest(self):
        return self.RawRequest

    def GetStatus(self):
        return self.Status

    def GetCookies(self):
        """Returns a list of easy to use Cookie objects.

        It avoids parsing string each time, etc

        """
        return cookie_factory.CookieFactory().CreateCookiesFromStr(
            self.CookieString)

    def GetResponseHeaders(self):
        return self.ResponseHeaders

    def GetRawResponse(self, WithStatus=True):
        try:
            return self.GetStatus() + "\r\n" + str(self.ResponseHeaders) + \
                   "\n\n" + self.ResponseContents
        except UnicodeDecodeError:
            return self.GetStatus() + "\r\n" + str(self.ResponseHeaders) + \
                   "\n\n" + "[Binary Content]"

    def GetRawResponseHeaders(self, WithStatus=True):
        return self.GetStatus() + "\r\n" + str(self.ResponseHeaders)

    def GetRawResponseBody(self):
        return self.ResponseContents

    def ImportProxyRequestResponse(self, request, response):
        self.IsInScope = request.in_scope
        self.URL = request.url
        self.InitData(request.body)
        self.Method = request.method
        try:
            self.Status = str(response.code) + " " + \
                          response_messages[int(response.code)]
        except KeyError:
            self.Status = str(response.code) + " " + "Unknown Error"
        self.RawRequest = request.raw_request
        self.ResponseHeaders = response.header_string
        self.ResponseContents = response.body
        self.Time = str(response.request_time)
        self.TimeHuman = self.Timer.GetTimeAsStr(self.Time)
        self.Found = (self.Status == "200 OK")
        # Cookie string for GetCookies method
        cookies_list = []
        for name, value in response.headers.iteritems():
            if name == "Set-Cookie":
                cookies_list.append(value.strip())
        self.CookieString = ','.join(cookies_list)
        self.New = True
        self.ID = ''
        self.HTMLLinkToID = ''
