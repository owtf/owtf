#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools & facilitate pentesting
Copyright (c) 2013, Abraham Aranguren <name.surname@gmail.com>  http://7-a.org
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

# Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in)
#                     as a part of Google Summer of Code 2013
'''
import json as pickle
import re
import os
import hashlib
from framework.lib.filelock import FileLock

class CacheHandler(object):
    """
    This class will be used by the request handler to
    either load or dump to cache. Main things that are done
    here :-
    * The request_hash is generated here
    * The file locks are managed here
    * .rd files are created here
    """
    def __init__(self, cache_dir, request, cookie_regex, blacklist):
        # Initialized with the root cache directory, HTTP request object, cookie_regex, blacklist boolean
        self.request = request
        self.cache_dir = cache_dir
        self.cookie_regex = cookie_regex
        self.blacklist = blacklist

    def calculate_hash(self, callback=None):
        # Based on blacklist boolean the cookie regex is used for filtering of cookies in request_hash
        # generation. However the original request is untampered.
        cookie_string = ''
        try:
            if self.blacklist:
                string_with_spaces = re.sub(self.cookie_regex, '', self.request.headers['Cookie']).strip()
                cookie_string = ''.join(string_with_spaces.split(' '))
            else:
                cookies_matrix = re.findall(self.cookie_regex, self.request.headers['Cookie'])
                for cookie_tuple in cookies_matrix:
                    for item in cookie_tuple:
                        if item:
                            cookie_string += item.strip()
        except KeyError:
            pass
        request_mod = self.request.method + self.request.url + self.request.version
        request_mod = request_mod + self.request.body + cookie_string

        # To support proxying of ua-tester
        try:
            request_mod = request_mod + self.request.headers["User-Agent"]
        except KeyError:
            pass

        # Websocket caching technique
        try:
            request_mod = request_mod + self.request.headers["Sec-Websocket-Key"]
        except KeyError:
            pass

        md5_hash = hashlib.md5()
        md5_hash.update(request_mod)
        self.request_hash = md5_hash.hexdigest()
        # This is the path to file inside url folder. This can be used for updating a html file
        self.file_path = os.path.join(self.cache_dir, 'url', self.request_hash)
        if callback:
            callback(self.request_hash)

    def create_response_object(self):
        return response_from_cache(self.request_hash, self.cache_dir)
                
    def dump(self, response):
        # This function takes in a HTTPResponse object and dumps the request
        # and response data. It also creates a .rd file with same file name
        # This is used by transaction logger 
        """
        cache_dict = {
                            'request_method':self.request.method,
                            'request_url':self.request.url,
                            'request_version':self.request.version,
                            'request_headers':self.request.headers,
                            'request_body':self.request.body,
                            'response_code':response.code,
                            'response_headers':response.headers,
                            'response_body':self.request.response_buffer
                     }
        """
        #cache_file = open(self.file_path, 'wb')
        #pickle.dump(cache_dict, cache_file)
        #cache_file.close()
        
        # The whole request and response is saved across 6 folder -
        # url, req-headers, req-body, resp-code, resp-headers, resp-body
        url_file = open(self.file_path, 'w')
        url_file.write("%s %s %s"%(self.request.method, self.request.url, self.request.version))
        url_file.close()
        
        reqHeaders_file = open(os.path.join(self.cache_dir, 'req-headers', self.request_hash), 'w')
        #reqHeaders_string = ''
        for name, value in self.request.headers.iteritems():
            reqHeaders_file.write("%s: %s\r\n"%(name, value))
            #reqHeaders_string += ("%s: %s\r\n"%(name, value))
        #reqHeaders_file.write(reqHeaders_string)
        reqHeaders_file.close()

        reqBody_file = open(os.path.join(self.cache_dir, 'req-body', self.request_hash), 'w')
        reqBody_file.write(self.request.body)
        reqBody_file.close()

        resCode_file = open(os.path.join(self.cache_dir, 'resp-code', self.request_hash), 'w')
        resCode_file.write(str(response.code))
        resCode_file.close()
                
        resHeaders_file = open(os.path.join(self.cache_dir, 'resp-headers', self.request_hash), 'w')
        #resHeaders_string = ''
        for name, value in response.headers.iteritems():
            resHeaders_file.write("%s: %s\r\n"%(name, value))
            #resHeaders_string += "%s: %s\r\n"%(name, value)
        #resHeaders_file.write(resHeaders_string)
        resHeaders_file.close()
        
        resBody_file = open(os.path.join(self.cache_dir, 'resp-body', self.request_hash), 'w')
        try:
            resBody_file.write(self.request.response_buffer)
        except:
            resBody_file = open(os.path.join(self.cache_dir, 'resp-body', self.request_hash), 'wb')
            resBody_file.write(self.request.response_buffer)
        finally:
            resBody_file.close()
        
        reqTime_file = open(os.path.join(self.cache_dir, 'resp-time', self.request_hash), 'w')
        reqTime_file.write("%s"%(str(response.request_time)))
        
        # This approach can be used as an alternative for object sharing
        # This creates a file with hash as name and .rd as extension
        open(self.file_path + '.rd', 'w').close()
        self.file_lock.release()
    
    def load(self):
        # This is the function which is called for every request. If file is not
        # found in cache, then a file lock is created for that and a None is
        # returned.
        """
        self.file_lock = FileLock(self.file_path)
        self.file_lock.acquire()
        """
        try:
            dummy = self.file_path
        except Exception:
            self.calculate_hash()
        finally:
            if os.path.isfile(self.file_path):
                return(self.create_response_object())
            else:
                self.file_lock = FileLock(self.file_path)
                self.file_lock.acquire()
                
                # For handling race conditions
                if os.path.isfile(self.file_path):
                    self.file_lock.release()
                    return(self.create_response_object())
                else:
                    return None

class DummyObject(object):
    """
    This class is just used to create a fake response objects
    """
    def __init__(self):
        self.dummy_obj = True

def response_from_cache(request_hash, cache_dir):
    # A fake response object is created with necessary attributes
    #cache_dict = pickle.load(open(self.file_path, 'rb'))
    dummyResponse = DummyObject()
    # The request-response saved across 6 unique folders is retrieved in following snippet
    # transactions/resp-code/
    dummyResponse.code = int(open(os.path.join(cache_dir, 'resp-code', request_hash), 'r').read())
    
    # transactions/resp-headers/
    response_headers = {}
    resHeaders = open(os.path.join(cache_dir, 'resp-headers', request_hash), 'r').readlines()
    for line in resHeaders:
        name, value = line.split(":", 1)
        response_headers[name] = value.strip()
    dummyResponse.headers = response_headers
    
    # transactions/resp-body
    dummyResponse.body = open(os.path.join(cache_dir, 'resp-body', request_hash), 'r').read()

    # Time taken for getting the response
    dummyResponse.request_time = float(open(os.path.join(cache_dir, 'resp-time', request_hash), 'r').read())

    # Extra attrs
    dummyResponse.header_string = open(os.path.join(cache_dir, 'resp-headers', request_hash), 'r').read()

    # Temp object is created as an alternative to use lists (or) dictionaries for passing values
    return dummyResponse

def request_from_cache(request_hash, cache_dir):
    # A fake request object is created with necessary attributes
    dummyRequest = DummyObject()
    # The request-response saved across 6 unique folders is retrieved in following snippet
    # transactions/url/
    dummyRequest.method, dummyRequest.url, dummyRequest.version = open(os.path.join(cache_dir, 'url', request_hash), 'r').read().split(' ')
    
    # transactions/req-headers/
    request_headers = {}
    reqHeaders = open(os.path.join(cache_dir, 'req-headers', request_hash), 'r').readlines()
    for line in reqHeaders:
        name, value = line.split(":", 1)
        request_headers[name] = value.strip()
    dummyRequest.headers = request_headers
    
    # transactions/resp-body
    dummyRequest.body = open(os.path.join(cache_dir, 'req-body', request_hash), 'r').read()
    
    # Extra attrs
    dummyRequest.raw_request = open(os.path.join(cache_dir, 'url', request_hash), 'r').read() + "\r\n"
    dummyRequest.raw_request += open(os.path.join(cache_dir, 'req-headers', request_hash), 'r').read() + "\r\n"
    if dummyRequest.body:
        dummyRequest.raw_request += open(os.path.join(cache_dir, 'req-body', request_hash), 'r').read() + "\r\n\r\n"
    # Temp object is created as an alternative to use lists (or) dictionaries for passing values
    return dummyRequest
