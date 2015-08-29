#!/usr/bin/env python
"""
HTTP_Transaction is a container of useful HTTP Transaction information to
simplify code both in the framework and the plugins.
"""

import cgi
import logging
import StringIO
import gzip,zlib
from httplib import responses as response_messages
import json

from framework import timer
from framework.lib.general import *
from framework.http.cookies.cookies import Cookies, Cookie


class HTTP_Transaction(object):
    def __init__(self, Timer):
        self.Timer = Timer
        self.New = False

    def ScopeToStr(self):
        return str(self.IsInScope)[0]

    def InScope(self):
        return(self.IsInScope)

    def Start(self, url, data, method, is_in_scope):
        self.IsInScope = is_in_scope
        self.StartRequest()
        self.URL = url
        self.InitData(data)
        self.Method = DeriveHTTPMethod(method, data)
        self.Found = None
        self.RawRequest = ''
        self.ResponseHeaders = []
        self.ResponseSize = ''
        self.Status = ''
        self.ID = ''
        self.HTMLLinkToID = ''
        self.New = True  # Flag new transaction.

    def InitData(self, data):
        self.Data = data
        if self.Data is None:
            # This simplifies other code later, no need to cast to str if None,
            # etc.
            self.Data = ''

    def StartRequest(self):
        self.Timer.start_timer('Request')
        self.Time = self.TimeHuman = ''

    def EndRequest(self):
        self.Time = self.Timer.get_elapsed_time_as_str('Request')
        self.TimeHuman = self.Time
        self.LocalTimestamp = self.Timer.get_current_date_time()

    def SetTransaction(self, found, request, response):
        # Response can be "Response" for 200 OK or "Error" for everything else,
        # we don't care here.
        if self.URL != response.url:
            if response.code not in [302, 301]:  # No way, error in hook.
                # Mark as a redirect, dirty but more accurate than 200 :P
                self.Status = str(302) + " Found"
                self.Status += " --Redirect--> " + str(response.code) + " "
                self.Status += response.msg
            # Redirect differs in schema (i.e. https instead of http).
            if self.URL.split(':')[0] != response.url.split(':')[0]:
                pass
            self.URL = response.url
        else:
            self.Status = str(response.code)+" "+response.msg
        self.RawRequest = request
        self.Found = found
        self.ResponseHeaders = response.headers
        self.ResponseContents = response.read()
        self.checkIfCompressed(response, self.ResponseContents) # a new self.Decodedcontent is added if the received response is in compressed format

        self.EndRequest()

    def SetTransactionFromDB(self,
                             id,
                             url,
                             method,
                             status,
                             time,
                             time_human,
                             local_timestamp,
                             request_data,
                             raw_request,
                             response_headers,
                             response_size,
                             response_body):
        self.ID = id
        self.New = False  # Flag NOT new transaction.
        self.URL = url
        self.Method = method
        self.Status = status
        self.Found = (self.Status == "200 OK")
        self.Time = time
        self.TimeHuman = time_human
        self.LocalTimestamp = local_timestamp
        self.Data = request_data
        self.RawRequest = raw_request
        self.ResponseHeaders = response_headers
        self.ResponseSize = response_size
        self.ResponseContents = response_body
        cookies_list = [
            header.split(':', 1)[-1].strip()
            for header in self.ResponseHeaders.split('\n')
            if header.split(':',1)[0].strip() == "Set-Cookie"]
        self.CookieString = ','.join(cookies_list)

    def GetSessionTokens(self):
        """
        * This forms a valid `Cookie` object (in form of a dict),
          so that it can be parsed and reused.
        * Takes an input a `CookieString` and parses the multiple cookies
          into separate dict objects.
        """
        try:
            cookie_ls = []
            # returns a list of cookies and their attributes
            for cookie in self.CookieString.split(","):
                cookie_ls.append(Cookie.from_string("Set-Cookie: {}".format(cookie)))

            cookies = []
            for i in range(len(cookie_ls)):
                cookies.append({"name": cookie_ls[i].name,
                                "value": str(cookie_ls[i].value),
                                "attributes": cookie_ls[i].attributes()
                            })
            return json.dumps(cookies)
        except:
            pass

    def SetError(self, error_message):
        # Only called for unknown errors, 404 and other HTTP stuff handled on
        # self.SetResponse.
        self.ResponseContents = error_message
        self.EndRequest()

    def GetID(self):
        return (self.ID)

    def SetID(self, id, html_link_to_id):
        self.ID = id
        self.HTMLLinkToID = html_link_to_id
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

    def GetHTMLLink(self, link_name=''):
        if '' == link_name:
            link_name = "Transaction " + self.ID
        return self.HTMLLinkToID.replace('@@@PLACE_HOLDER@@@', link_name)

    def GetHTMLLinkWithTime(self, link_name=''):
        return self.GetHTMLLink(link_name) + " (" + self.TimeHuman + ")"

    def GetRawEscaped(self):
        return "<pre>" + cgi.escape(self.GetRaw()) +"</pre>"

    def GetRaw(self):
        return self.GetRawRequest() + "\n\n" + self.GetRawResponse()

    def GetRawRequest(self):
        return self.RawRequest

    def GetStatus(self):
        return self.Status

    def GetResponseHeaders(self):
        return self.ResponseHeaders

    def GetRawResponse(self, with_status=True):
        try:
            return self.GetStatus() + "\r\n" + str(self.ResponseHeaders) + \
                   "\n\n" + self.ResponseContents
        except UnicodeDecodeError:
            return self.GetStatus() + "\r\n" + str(self.ResponseHeaders) + \
                   "\n\n" + "[Binary Content]"

    def GetRawResponseHeaders(self, with_status=True):
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
        self.ResponseSize = len(self.ResponseContents)
        self.Time = str(response.request_time)
        self.TimeHuman = self.Timer.get_time_human(self.Time)
        self.LocalTimestamp = request.local_timestamp
        self.Found = (self.Status == "200 OK")
        # Cookie string for GetCookies method
        cookies_list = [
            value.strip()
            for name, value in response.headers.iteritems()
            if name == "Set-Cookie"]
        self.CookieString = ','.join(cookies_list)
        self.New = True
        self.ID = ''
        self.HTMLLinkToID = ''

    def getDecodedResponse(self):
        return self.DecodedResponse

    def checkIfCompressed(self, response, content):
        if response.info().get('Content-Encoding') == 'gzip':  # check for gzip compression
            compressedFile = StringIO.StringIO()
            compressedFile.write(content)
            compressedFile.seek(0)
            f = gzip.GzipFile(fileobj=compressedFile, mode='rb')
            self.DecodedContent = f.read()
        elif response.info().get('Content-Encoding') == 'deflate':  # check for deflate compression
            self.DecodedContent = zlib.decompress(content)
        else:
            self.DecodedContent = content  # else the no compression
