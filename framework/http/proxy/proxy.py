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

The Proxy module sets up a listener and performs all requests through the framework requester
'''
from twisted.web import server, resource
from twisted.internet import reactor
from framework.lib.general import *
# twisted webclient:
from twisted.internet import reactor
from twisted.web.client import getPage, _parse, HTTPClientFactory
import twisted.internet as internet
import twisted.internet.defer
import twisted.internet.threads
import time
from twisted.internet.defer import DeferredSemaphore, DeferredQueue

class Proxy(resource.Resource):
	isLeaf = True

	def __init__(self, Requester, Semaphore, Queue):
		self.Requester = Requester
		self.Semaphore = Semaphore
		self.Queue = Queue
		
	def getPage(url, contextFactory=None, *args, **kwargs):
		url = str(url)
		scheme, host, port, path = _parse(url)
		factory = HTTPClientFactory(url, *args, **kwargs)
		if False: # use a proxy
			host, port = 'proxy', 6060
			factory.path = url
		if scheme == 'https':
			from twisted.internet import ssl
		if contextFactory is None:
			contextFactory = ssl.ClientContextFactory()
			reactor.connectSSL(host, port, factory, contextFactory)
		else:
			reactor.connectTCP(host, port, factory)
		return factory.deferred

	def render_GET(self, request):
		#return request.received_headers
		#p(request)
		cprint("Sending GET request to Requester: " + request.uri)
		#return self.getPage(str(request.uri))
		#return getPage(request.uri).addCallbacks(self.RequestSuccessful, self.RequestFailed)
		#reactor.run()
		d = internet.defer.Deferred()
		internet.defer.setDebugging(True)
		#d.addBoth(self.showResult)
		#d = internet.threads.deferToThread(self.blockingFunction, 1.75, 2.25)
		d.addCallback(self.QueueResult, request)
		#d.addCallback(self.showResult, request)
		d.addErrback(self.showError, request)
		internet.reactor.callLater(0, d.callback, '')
		return server.NOT_DONE_YET
		Transaction = self.Requester.GetTransaction(False, request.uri, 'GET')
		return Transaction.GetRawResponseBody()
		return '<html>Test</html>'
		#pprint.PrettyPrinter(indent=4,depth=1).pprint(request)
		#pprint.PrettyPrinter(indent=4,depth=4).pprint(request)
		#return dir(request)    
		#return "<html>Hello, world!</html>"
		
	def blockingFunction(self, crap1, crap2):
		time.sleep(3)
		
	def QueueResult(self, result, request):
		self.Semaphore.run(self.showResult(result, request))
		#self.Queue.put(self.showResult(result, request))
		# Review: http://stackoverflow.com/questions/2861858/queue-remote-calls-to-a-python-twisted-perspective-broker
		#self.Queue.
		
	def showResult(self, result, request):
		Transaction = self.Requester.GetTransaction(False, request.uri, 'GET')
		request.write(Transaction.GetRawResponseBody())
		request.finish
		return ''
		request.write(str(result))
		request.finish()
  
	def showError(self, err, request):
		request.write(str(err))
		request.finish()
		
	def RequestSuccessful(self, results):
		return dir(results)
	
	def RequestFailed(self, results, failureMessage="Call Failed"):
		return dir(results)

class ProxyServer:
	def __init__(self, Requester, ProxyOptions):
		self.Requester = Requester
		self.ProxyOptions = ProxyOptions
		if None != self.ProxyOptions:
			self.SetupProxy()

	def SetupProxy(self):
		if len(self.ProxyOptions) == 2:
			self.Interface, self.Port = self.ProxyOptions.split(':')
		else: # Only the port was passed
			self.Port = self.ProxyOptions[0]
			# If the interface was not specified listen on 127.0.0.1 only:
			self.Interface = "127.0.0.1"
			print "Interface=" + str(self.Interface)
		print "Port=" + str(self.Port)
		cprint("Setting up Proxy listener on " + self.Interface + ':' + self.Port) 
		self.Port = int(self.Port)
		self.Semaphore = DeferredSemaphore(1)
		self.Queue = DeferredQueue
		self.Proxy = Proxy(self.Requester, self.Semaphore, self.Queue)
		self.Site = server.Site(self.Proxy)
		reactor.listenTCP(self.Port, self.Site, interface=self.Interface)
		reactor.run()
"""
site = server.Site(Simple())
reactor.listenTCP(8080, site)
reactor.run()
"""