#!/usr/bin/env python
"""
The Requester module is in charge of simplifying HTTP requests and
automatically log HTTP transactions by calling the DB module.
"""

import sys
import cgi
import httplib
import logging
import urllib
import urllib2
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import RequesterInterface

from framework.http import transaction
from framework.lib.general import *


# Intercept raw request trick from:
# http://stackoverflow.com/questions/6085709/get-headers-sent-in-urllib2-http-request
class MyHTTPConnection(httplib.HTTPConnection):
    def send(self, s):
        global raw_request
        # Saving to global variable for Requester class to see.
        raw_request.append(s)
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
        global raw_request
        # Saving to global variable for Requester class to see.
        raw_request.append(s)
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


class Requester(BaseComponent, RequesterInterface):

    COMPONENT_NAME = "requester"

    def __init__(self, proxy):
        self.register_in_service_locator()
        self.db_config = self.get_component("db_config")
        self.target = self.get_component("target")
        self.transaction = self.get_component("transaction")
        self.url_manager = self.get_component("url_manager")
        self.error_handler = self.get_component("error_handler")
        self.plugin_handler = self.get_component("plugin_handler")
        self.timer = self.get_component("timer")
        self.http_transaction = None
        self.Headers = {'User-Agent': self.db_config.Get('USER_AGENT')}
        self.RequestCountRefused = 0
        self.RequestCountTotal = 0
        self.LogTransactions = False
        self.Proxy = proxy
        if proxy is None:
            logging.debug(
                "WARNING: No outbound proxy selected. It is recommended to "
                "use an outbound proxy for tactical fuzzing later")
            self.Opener = urllib2.build_opener(
                MyHTTPHandler,
                MyHTTPSHandler,
                # FIXME: "Smart" redirect handler not really working.
                SmartRedirectHandler)
        else:  # All requests must use the outbound proxy.
            logging.debug("Setting up proxy(inbound) for OWTF requests..")
            ip, port = proxy
            proxy_conf = {
                'http': 'http://' + ip + ":" + port,
                'https': 'http://' + ip + ":" + port}
            proxy_handler = urllib2.ProxyHandler(proxy_conf)
            self.Opener = urllib2.build_opener(
                proxy_handler,
                MyHTTPHandler,
                MyHTTPSHandler,
                # FIXME: Works except no raw request on https.
                SmartRedirectHandler)
        urllib2.install_opener(self.Opener)

    def log_transactions(self, log_transactions=True):
        backup = self.LogTransactions
        self.LogTransactions = log_transactions
        return backup

    def NeedToAskBeforeRequest(self):
        return not self.plugin_handler.NormalRequestsAllowed()

    def IsTransactionAlreadyAdded(self, url):
        return self.transaction.IsTransactionAlreadyAdded({'url': url.strip()})

    def is_request_possible(self):
        return self.plugin_handler.RequestsPossible()

    def ProxyCheck(self):
        # Verify proxy works! www.google.com might not work in a restricted
        # network, try target URL :)
        if self.Proxy is not None and self.is_request_possible():
            url = self.db_config.Get('PROXY_CHECK_URL')
            refused_before = self.RequestCountRefused
            cprint(
                "Proxy Check: Avoid logging request again if already in DB..")
            log_setting_backup = False
            if self.IsTransactionAlreadyAdded(url):
                log_setting_backup = self.log_transactions(False)
            if log_setting_backup:
                self.log_transactions(log_setting_backup)
            refused_after = self.RequestCountRefused
            if refused_before < refused_after:  # Proxy is refusing connections.
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

    def SetHeaders(self, headers):
        self.Headers = headers

    def SetHeader(self, header, value):
        self.Headers[header] = value

    def StringToDict(self, string):
        dict = defaultdict(list)
        count = 0
        prev_item = ''
        for item in string.strip().split('='):
            if count % 2 == 1:  # Key.
                dict[prev_item] = item
            else:  # Value.
                dict[item] = ''
                prev_item = item
            count += 1
        return dict

    def DerivePOSTToStr(self, post=None):
        post = self.DerivePOST(post)
        if post is None:
            return ''
        return post

    def DerivePOST(self, post=None):
        if '' == post:
            post = None
        if post is not None:
            if isinstance(post, str) or isinstance(post, unicode):
                # Must be a dictionary prior to urlencode.
                post = self.StringToDict(post)
            post = urllib.urlencode(post)
        return post

    def perform_request(self, request):
        return urllib2.urlopen(request)

    def set_succesful_transaction(self, raw_request, response):
        return self.http_transaction.SetTransaction(True, raw_request[0], response)

    def log_transaction(self):
        self.transaction.LogTransaction(self.http_transaction)

    def Request(self, url, method=None, post=None):
        # kludge: necessary to get around urllib2 limitations: Need this to get
        # the exact request that was sent.
        global raw_request
        url = str(url)

        raw_request = []  # Init Raw Request to blank list.
        post = self.DerivePOST(post)
        method = DeriveHTTPMethod(method, post)
        url = url.strip()  # Clean up URL.
        request = urllib2.Request(url, post, self.Headers)  # GET request.
        if method is not None:
            # kludge: necessary to do anything other that GET or POST with
            # urllib2
            request.get_method = lambda : method
        # MUST create a new Transaction object each time so that lists of
        # transactions can be created and process at plugin-level
        # Pass the timer object to avoid instantiating each time.
        self.http_transaction = transaction.HTTP_Transaction(self.timer)
        self.http_transaction.Start(
            url,
            post,
            method,
            self.target.IsInScopeURL(url))
        self.RequestCountTotal += 1
        try:
            response = self.perform_request(request)
            self.set_succesful_transaction(raw_request, response)
        except urllib2.HTTPError, Error:  # page NOT found.
            # Error is really a response for anything other than 200 OK in
            # urllib2 :)
            self.http_transaction.SetTransaction(False, raw_request[0], Error)
        except urllib2.URLError, Error:  # Connection refused?
            err_message = self.ProcessHTTPErrorCode(Error, url)
            self.http_transaction.SetError(err_message)
        except IOError:
            err_message = "ERROR: Requester Object -> Unknown HTTP " \
                           "Request error: " + url + "\n" + str(sys.exc_info())
            self.http_transaction.SetError(err_message)
        if self.LogTransactions:
            # Log transaction in DB for analysis later and return modified
            # Transaction with ID.
            self.log_transaction()
        return self.http_transaction

    def ProcessHTTPErrorCode(self, error, url):
        message = ""
        if str(error.reason).startswith("[Errno 111]"):
            message = "ERROR: The connection was refused!: " +  str(error)
            self.RequestCountRefused += 1
        elif str(error.reason).startswith("[Errno -2]"):
            self.error_handler.FrameworkAbort(
                "ERROR: cannot resolve hostname!: " + str(error))
        else:
            message = "ERROR: The connection was not refused, unknown error!"
        log = logging.getLogger('general')
        log.info(message)
        return message + " (Requester Object): " + url + \
               "\n" + str(sys.exc_info())

    def GET(self, url):
        return self.Request(url)

    def POST(self, url, data):
        return self.Request(url, 'POST', data)

    def TRACE(self, url):
        return self.Request(url, 'TRACE', None)

    def OPTIONS(self, url):
        return self.Request(url, 'OPTIONS', None)

    def HEAD(self, url):
        return self.Request(url, 'HEAD', None)

    def DEBUG(self, url):
        self.BackupHeaders()
        self.Headers['Command'] = 'start-debug'
        result = self.Request(url, 'DEBUG', None)
        self.RestoreHeaders()
        return result

    def PUT(self, url, content_type='text/plain'):
        self.BackupHeaders()
        self.Headers['Content-Type'] = content_type
        self.Headers['Content-Length'] = "0"
        result = self.Request(url, 'PUT', None)
        self.RestoreHeaders()
        return result

    def BackupHeaders(self):
        self.HeadersBackup = dict.copy(self.Headers)

    def RestoreHeaders(self):
        self.Headers = dict.copy(self.HeadersBackup)

    def GetTransaction(self, use_cache, url, method=None, data=None):
        criteria = {'url': url.strip()}
        if method is not None:
            criteria['method'] = method
        # Must clean-up data to ensure match is found.
        if data is not None:
            criteria['data'] = self.DerivePOSTToStr(data)
        # Visit URL if not already visited.
        if (not use_cache or not self.transaction.IsTransactionAlreadyAdded(criteria)):
            if method in ['', 'GET', 'POST', 'HEAD', 'TRACE', 'OPTIONS']:
                return self.Request(url, method, data)
            elif method == 'DEBUG':
                return self.DEBUG(url)
            elif method == 'PUT':
                return self.PUT(url, data)
        else:  # Retrieve from DB = faster.
            # Important since there is no transaction ID with transactions
            # objects created by Requester.
            return self.transaction.GetFirst(criteria)

    def GetTransactions(self,
                        use_cache,
                        url_list,
                        method=None,
                        data=None,
                        unique=True):
        transactions = []
        if unique:
            url_list = set(url_list)
        for url in url_list:
            url = url.strip()  # Clean up the URL first.
            if not url:
                continue  # Skip blank lines.
            if not self.url_manager.IsURL(url):
                self.error_handler.Add(
                    "Minor issue: " + str(url) + " is not a valid URL and "
                    "has been ignored, processing continues")
                continue  # Skip garbage URLs.
            transaction = self.GetTransaction(use_cache, url, method=method, data=data)
            if transaction is not None:
                transactions.append(transaction)
        return transactions
