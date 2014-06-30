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

The Requester module is in charge of simplifying HTTP requests and
automatically log HTTP transactions by calling the DB module.

"""

import sys
import cgi
import httplib
import logging
import urllib
import urllib2

from framework.http import transaction
from framework.lib.general import *


# Intercept raw request trick from:
# http://stackoverflow.com/questions/6085709/get-headers-sent-in-urllib2-http-request
class MyHTTPConnection(httplib.HTTPConnection):
    def send(self, s):
        global RawRequest
        # Saving to global variable for Requester class to see.
        RawRequest.append(s)
        httplib.HTTPConnection.send(self, s)


class MyHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        try:
            return self.do_open(MyHTTPConnection, req)
        except KeyboardInterrupt:
            raise KeyboardInterrupt  # Not handled here.
        except Exception, e:
            # Can't have OWTF crash due to a library exception -i.e. raise
            # BadStatusLine(line)-
            return ''


class MyHTTPSConnection(httplib.HTTPSConnection):
    def send(self, s):
        global RawRequest
        # Saving to global variable for Requester class to see.
        RawRequest.append(s)
        httplib.HTTPSConnection.send(self, s)


class MyHTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        try:
            return self.do_open(MyHTTPSConnection, req)
        except KeyboardInterrupt:
            raise KeyboardInterrupt  # Not handled here.
        except Exception, e:
            # Can't have OWTF crash due to a library exception -i.e. raise
            # BadStatusLine(line)-.
            return ''


# SmartRedirectHandler is courtesy of:
# http://www.diveintopython.net/http_web_services/redirects.html
class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


class Requester:
    def __init__(self, Core, Proxy):
        self.Core = Core
        self.Headers = {'User-Agent': self.Core.DB.Config.Get('USER_AGENT')}
        self.RequestCountRefused = 0
        self.RequestCountTotal = 0
        self.LogTransactions = False
        self.Proxy = Proxy
        if Proxy is None:
            cprint(
                "WARNING: No outbound proxy selected. It is recommended to "
                "use an outbound proxy for tactical fuzzing later")
            self.Opener = urllib2.build_opener(
                MyHTTPHandler,
                MyHTTPSHandler,
                # FIXME: "Smart" redirect handler not really working.
                SmartRedirectHandler)
        else:  # All requests must use the outbound proxy.
            cprint("Setting up proxy(inbound) for OWTF requests..")
            IP, Port = Proxy
            ProxyConf = {
                'http': 'http://' + IP + ":" + Port,
                'https': 'http://' + IP + ":" + Port}
            ProxyHandler = urllib2.ProxyHandler(ProxyConf)
            self.Opener = urllib2.build_opener(
                ProxyHandler,
                MyHTTPHandler,
                MyHTTPSHandler,
                # FIXME: Works except no raw request on https.
                SmartRedirectHandler)
        urllib2.install_opener(self.Opener)

    def log_transactions(self, LogTransactions=True):
        Backup = self.LogTransactions
        self.LogTransactions = LogTransactions
        return Backup

    def NeedToAskBeforeRequest(self):
        return not self.Core.PluginHandler.NormalRequestsAllowed()

    def IsTransactionAlreadyAdded(self, URL):
        return self.Core.DB.Transaction.IsTransactionAlreadyAdded({
            'url': URL.strip()})

    def is_request_possible(self):
        return self.Core.PluginHandler.RequestsPossible()

    def ProxyCheck(self):
        # Verify proxy works! www.google.com might not work in a restricted
        # network, try target URL :)
        if self.Proxy != None and self.is_request_possible():
            URL = self.Core.DB.Config.Get('PROXY_CHECK_URL')
            RefusedBefore = self.RequestCountRefused
            cprint("Proxy Check: Avoid logging request again if already in DB..")
            LogSettingBackup = False
            if self.IsTransactionAlreadyAdded(URL):
                LogSettingBackup = self.log_transactions(False)
            Transaction = self.GET(URL)
            if LogSettingBackup:
                self.log_transactions(LogSettingBackup)
            RefusedAfter = self.RequestCountRefused
            if RefusedBefore < RefusedAfter:  # Proxy is refusing connections.
                return [
                    False,
                    "ERROR: Proxy Check error: The proxy is not listening " \
                    "or is refusing connections"]
            else:
                return [
                    True,
                    "Proxy Check OK: The proxy appears to be working"]
        return [
            True,
            "Proxy Check OK: No proxy is setup or no HTTP requests will " \
            "be made"]

    def GetHeaders(self):
        return self.Headers

    def SetHeaders(self, Headers):
        self.Headers = Headers

    def SetHeader(self, Header, Value):
        self.Headers[Header] = Value

    def StringToDict(self, String):
        Dict = defaultdict(list)
        Count = 0
        PrevItem = ''
        for Item in String.strip().split('='):
            if Count % 2 == 1:  # Key.
                Dict[PrevItem] = Item
            else:  # Value.
                Dict[Item] = ''
                PrevItem = Item
            Count += 1
        return Dict

    def DerivePOSTToStr(self, POST = None):
        POST = self.DerivePOST(POST)
        if POST == None:
            return ''
        return POST

    def DerivePOST(self, POST = None):
        if '' == POST:
            POST = None
        if None != POST:
            if isinstance(POST, str) or isinstance(POST, unicode):
                # Must be a dictionary prior to urlencode.
                POST = self.StringToDict(POST)
            POST = urllib.urlencode(POST)
        return POST

    def perform_request(self, request):
        return urllib2.urlopen(request)

    def set_succesful_transaction(self, RawRequest, Response):
        return self.Transaction.SetTransaction(True, RawRequest[0], Response)

    def log_transaction(self):
        self.Core.DB.Transaction.LogTransaction(self.Transaction)

    def Request(self, URL, Method = None, POST = None):
        # kludge: necessary to get around urllib2 limitations: Need this to get
        # the exact request that was sent.
        global RawRequest
        URL = str(URL)

        RawRequest = []  # Init Raw Request to blank list.
        POST = self.DerivePOST(POST)
        Method = DeriveHTTPMethod(Method, POST)
        URL = URL.strip()  # Clean up URL.
        request = urllib2.Request(URL, POST, self.Headers)  # GET request.
        if None != Method:
            # kludge: necessary to do anything other that GET or POST with
            # urllib2
            request.get_method = lambda : Method
        # MUST create a new Transaction object each time so that lists of
        # transactions can be created and process at plugin-level
        # Pass the timer object to avoid instantiating each time.
        self.Transaction = transaction.HTTP_Transaction(self.Core.Timer)
        self.Transaction.Start(
            URL,
            POST,
            Method,
            self.Core.DB.Target.IsInScopeURL(URL))
        self.RequestCountTotal += 1
        try:
            Response = self.perform_request(request)
            self.set_succesful_transaction(RawRequest, Response)
        except urllib2.HTTPError, Error:  # page NOT found.
            # Error is really a response for anything other than 200 OK in
            # urllib2 :)
            self.Transaction.SetTransaction(False, RawRequest[0], Error)
        except urllib2.URLError, Error:  # Connection refused?
            ErrorMessage = self.ProcessHTTPErrorCode(Error, URL)
            self.Transaction.SetError(ErrorMessage)
        except IOError:
            ErrorMessage = "ERROR: Requester Object -> Unknown HTTP " \
                           "Request error: " + URL + "\n" + str(sys.exc_info())
            self.Transaction.SetError(ErrorMessage)
        if self.LogTransactions:
            # Log transaction in DB for analysis later and return modified
            # Transaction with ID.
            self.log_transaction()
        return self.Transaction

    def ProcessHTTPErrorCode(self, Error, URL):
        Message = ""
        if str(Error.reason).startswith("[Errno 111]"):
            Message = "ERROR: The connection was refused!: " +  str(Error)
            self.RequestCountRefused += 1 
        elif str(Error.reason).startswith("[Errno -2]"):
            self.Core.Error.FrameworkAbort(
                "ERROR: cannot resolve hostname!: " + str(Error))
        else:
            Message = "ERROR: The connection was not refused, unknown error!"
        log = logging.getLogger('general')
        log.info(Message)
        ErrorMessage = Message + " (Requester Object): " + URL + \
                       "\n" + str(sys.exc_info())
        return ErrorMessage

    def GET(self, URL):
        return self.Request(URL)

    def POST(self, URL, Data):
        return self.Request(URL, 'POST', Data)

    def TRACE(self, URL):
        return self.Request(URL, 'TRACE', None)

    def OPTIONS(self, URL):
        return self.Request(URL, 'OPTIONS', None)

    def HEAD(self, URL):
        return self.Request(URL, 'HEAD', None)

    def DEBUG(self, URL):
        self.BackupHeaders()
        self.Headers['Command'] = 'start-debug'
        Result = self.Request(URL, 'DEBUG', None)
        self.RestoreHeaders()
        return Result

    def PUT(self, URL, Data, ContentType = 'text/plain'):
        self.BackupHeaders()
        self.Headers['Content-Type'] = ContentType
        self.Headers['Content-Length'] = "0"
        Result = self.Request(URL, 'PUT', None)
        self.RestoreHeaders()
        return Result

    def BackupHeaders(self):
        self.HeadersBackup = dict.copy(self.Headers)

    def RestoreHeaders(self):
        self.Headers = dict.copy(self.HeadersBackup)

    def GetTransaction(self, UseCache, URL, Method = '', Data = ''):
        Criteria = {
            'url': URL.strip(),
            'method': Method,
            # Must clean-up data to ensure match is found.
            'data': self.DerivePOSTToStr(Data)}
        # Visit URL if not already visited.
        if (not UseCache or not
                self.Core.DB.Transaction.IsTransactionAlreadyAdded(Criteria)):
            if Method in [ '', 'GET', 'POST', 'HEAD', 'TRACE', 'OPTIONS' ]:
                return self.Request(URL, Method, Data)
            elif Method == 'DEBUG':
                return self.DEBUG(URL)
            elif Method == 'PUT':
                return self.PUT(URL, Data)
        else:  # Retrieve from DB = faster.
            # Important since there is no transaction ID with transactions
            # objects created by Requester.
            return self.Core.DB.Transaction.GetFirst(Criteria)

    def GetTransactions(self,
                        UseCache,
                        URLList,
                        Method='',
                        Data='',
                        Unique=True):
        Transactions = []
        if Unique:
            URLList = set(URLList)
        for URL in URLList:
            URL = URL.strip()  # Clean up the URL first.
            if not URL:
                continue  # Skip blank lines.
            if not self.Core.DB.URL.IsURL(URL):
                self.Core.Error.Add(
                    "Minor issue: " + str(URL) + " is not a valid URL and "
                    "has been ignored, processing continues")
                continue  # Skip garbage URLs.
            Transactions.append(self.GetTransaction(
                UseCache,
                URL,
                Method,
                Data))
        return Transactions
