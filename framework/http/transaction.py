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

HTTP_Transaction is a container of useful HTTP Transaction information to simplify code both in the framework and the plugins
'''
from framework import timer
from framework.lib.general import *
from framework.http.cookies import cookie_factory
import cgi

class HTTP_Transaction:
	def __init__(self, Timer):
		self.Timer = Timer
		self.New = False

	def ScopeToStr(self):
		return str(self.IsInScope)[0]

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
		self.New = True # Flag new transaction

	def InitData(self, Data):
		self.Data = Data
		if self.Data == None:
			self.Data = '' # This simplifies other code later, no need to cast to str if None, etc

	def StartRequest(self):
		self.Timer.StartTimer('Request')
		self.Time = self.TimeHuman = ''

	def EndRequest(self):
		self.Time = str(self.Timer.GetElapsedTime('Request'))
		self.TimeHuman = self.Timer.GetTimeAsStr(self.Time)

	def SetTransaction(self, Found, Request, Response): # Response can be "Response" for 200 OK or "Error" for everything else, we don't care here
		if self.URL != Response.url:
			if Response.code not in [ 302, 301 ]: # No way, error in hook
				self.Status = str(302)+" Found" # Mark as a redirect, dirty but more accurate than 200 :P
				self.Status += " --Redirect--> "+str(Response.code)+" "+Response.msg 
			if self.URL.split(':')[0] != Response.url.split(':')[0]: # Redirect differs in schema (i.e. https instead of http)
				pass
				#self.IsInScope = False --> Breaks links, to be fixed in some next release
			self.URL = Response.url
		else:
			self.Status = str(Response.code)+" "+Response.msg
		self.RawRequest = Request
		self.Found = Found
		self.ResponseHeaders = Response.headers
		#p(self.ResponseHeaders)
		self.ResponseContents = Response.read()
		self.EndRequest()

	def SetTransactionFromDB(self, IndexRec, Request, ResponseHeaders, ResponseBody):
		self.New = False # Flag NOT new transaction
		self.Time = IndexRec['Time']
		self.TimeHuman = IndexRec['TimeHuman']
		self.Status = IndexRec['Status']
		self.Found = (self.Status == "200 OK")
		self.Method = IndexRec['Method']
		self.URL = IndexRec['URL']
		self.Data = IndexRec['Data']
		self.RawRequest = Request
		#self.ResponseHeaders = ResponseHeaders.split("\n")
		self.ResponseHeaders = ResponseHeaders
		self.ResponseContents = ResponseBody

	def SetError(self, ErrorMessage): # Only called for unknown errors, 404 and other HTTP stuff handled on self.SetResponse
		self.ResponseContents = ErrorMessage
		self.EndRequest()

	def SetID(self, ID, HTMLLinkToID):
		self.ID = ID
		self.HTMLLinkToID = HTMLLinkToID
		if self.New: # Only for new transactions, not when retrieved from DB, etc
			cprint("New owtf HTTP Transaction: "+" - ".join([self.ID, self.TimeHuman, self.Status, self.Method, self.URL]))

	def GetHTMLLink(self, LinkName = ''):
		if '' == LinkName:
			LinkName = "Transaction "+self.ID
		return self.HTMLLinkToID.replace('@@@PLACE_HOLDER@@@', LinkName)

	def GetHTMLLinkWithTime(self, LinkName = ''):
		return self.GetHTMLLink(LinkName)+" ("+self.TimeHuman+")"

	def GetRawEscaped(self):
		return "<pre>"+cgi.escape(self.GetRaw())+"</pre>"

	def GetRaw(self):
		return self.GetRawRequest()+"\n\n"+self.GetRawResponse()

	def GetRawRequest(self):
		return self.RawRequest

	def GetStatus(self, WithStatus = True):
		Status = ''
		if WithStatus:
			Status = self.Status+"\n"
		return Status

	def GetCookies(self): # Returns a list of easy to use Cookie objects to avoid parsing string each time, etc
		return cookie_factory.CookieFactory().CreateCookiesFromStr(self.GetResponseHeaders().getheader('Set-Cookie'))

	def GetResponseHeaders(self):
		return self.ResponseHeaders

	def GetRawResponse(self, WithStatus = True):
		return self.GetStatus(WithStatus)+str(self.ResponseHeaders)+"\n\n"+self.ResponseContents

	def GetRawResponseHeaders(self, WithStatus = True):
		return self.GetStatus(WithStatus)+str(self.ResponseHeaders)

	def GetRawResponseBody(self):
		return self.ResponseContents

