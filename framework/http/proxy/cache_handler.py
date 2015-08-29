#!/usr/bin/env python
'''
# Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in)
#                     as a part of Google Summer of Code 2013
'''
import re
import os
import json
import base64
import hashlib
import datetime
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
        self.file_path = os.path.join(self.cache_dir, self.request_hash)
        if callback:
            callback(self.request_hash)

    def create_response_object(self):
        return response_from_cache(os.path.join(self.cache_dir, self.request_hash))

    def dump(self, response):
        # This function takes in a HTTPResponse object and dumps the request
        # and response data. It also creates a .rd file with same file name
        # This is used by transaction logger
        try:
            response_body = unicode(self.request.response_buffer, "utf-8")
            binary_response = False
        except UnicodeDecodeError:
            response_body = base64.b64encode(self.request.response_buffer)
            binary_response = True
        cache_dict = {
                            'request_method':self.request.method,
                            'request_url':self.request.url,
                            'request_version':self.request.version,
                            'request_headers':self.request.headers,
                            'request_body':self.request.body,
                            'request_time':response.request_time,
                            'request_local_timestamp':self.request.local_timestamp.isoformat(),
                            'response_code':response.code,
                            'response_headers':response.headers,
                            'response_body':response_body,
                            'binary_response':binary_response
                     }
        with open(self.file_path, 'w') as outfile:
            json.dump(cache_dict, outfile)

        # This approach can be used as an alternative for object sharing
        # This creates a file with hash as name and .rd as extension
        open(self.file_path + '.rd', 'w').close()
        self.file_lock.release()

    def load(self):
        # This is the function which is called for every request. If file is not
        # found in cache, then a file lock is created for that and a None is
        # returned.
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

def response_from_cache(file_path):
    # A fake response object is created with necessary attributes
    #cache_dict = pickle.load(open(self.file_path, 'rb'))
    dummyResponse = DummyObject()
    cache_dict = json.loads(open(file_path, 'r').read())
    dummyResponse.code = cache_dict["response_code"]
    dummyResponse.headers = cache_dict["response_headers"]
    dummyResponse.header_string = '\r\n'.join(["%s: %s" % (name, value) for name, value in cache_dict["response_headers"].iteritems()])
    if cache_dict["binary_response"] == True:
        dummyResponse.body = base64.b64decode(cache_dict["response_body"])
    else:
        dummyResponse.body = cache_dict["response_body"]
    dummyResponse.request_time = cache_dict["request_time"]

    # Temp object is created as an alternative to use lists (or) dictionaries for passing values
    return dummyResponse

def request_from_cache(file_path):
    # A fake request object is created with necessary attributes
    dummyRequest = DummyObject()
    cache_dict = json.loads(open(file_path, 'r').read())
    dummyRequest.local_timestamp = datetime.datetime.strptime(cache_dict["request_local_timestamp"].strip("\r\n"), '%Y-%m-%dT%H:%M:%S.%f')
    dummyRequest.method = cache_dict["request_method"]
    dummyRequest.url = cache_dict["request_url"]
    dummyRequest.headers = cache_dict["request_headers"]
    dummyRequest.body = cache_dict["request_body"]
    dummyRequest.raw_request = "%s %s %s\r\n" % (cache_dict["request_method"], cache_dict["request_url"], cache_dict["request_version"])
    for name, value in cache_dict["request_headers"].iteritems():
        dummyRequest.raw_request += "%s: %s\r\n" % (name, value)
    if cache_dict["request_body"]:
        dummyRequest.raw_request += cache_dict["request_body"] + "\r\n\r\n"
    return dummyRequest
