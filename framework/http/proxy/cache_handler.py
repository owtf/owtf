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
import cPickle as pickle
import os
import hashlib
from filelock import FileLock

class CacheHandler(object):
    """
    This class will be used by the request handler to
    either load or dump to cache. Main things that are done
    here :-
    * The request_hash is generated here
    * The file locks are managed here
    * .rd files are created here
    """
    
    def __init__(self, cache_dir, request):
        # Initialized with the root cache directory and HTTP request object
        self.request = request
        self.cache_dir = cache_dir
        request_mod = request.method + ' ' + request.full_url() + ' ' + request.version
        request_mod = request_mod + request.body
        
        md5_hash = hashlib.md5()
        md5_hash.update(request_mod)
        self.request_hash = md5_hash.hexdigest()
        
        self.file_path = os.path.join(self.cache_dir, self.request_hash)

    def create_response_object(self):
        # A fake response object is created with necessary attributes so 
        # that only one handle_response function can handle both cached 
        # and normal responses
        cache_dict = pickle.load(open(self.file_path, 'rb'))
        return DummyResponse(cache_dict['response_code'], cache_dict['response_headers'], cache_dict['response_body'])
                
    def dump(self, response):
        # This function takes in a HTTPResponse object and dumps the request
        # and response data. It also creates a .rd file with same file name
        # This is used by transaction logger process
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
        cache_file = open(self.file_path, 'wb')
        pickle.dump(cache_dict, cache_file)
        cache_file.close()
        self.file_lock.release()
        open(self.file_path + '.rd', 'w').close()
    
    def load(self):
        # This is the function which is called for every request. If file is not
        # found in cache, then a file lock is created for that and a None is
        # returned.
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

class DummyResponse(object):
    """
    This class is just used to create a fake response object
    """
    def __init__(self, response_code, response_headers, response_body):
        self.code = response_code
        self.headers = response_headers
        self.body = response_body
