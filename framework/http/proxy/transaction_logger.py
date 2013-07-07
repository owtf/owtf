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
from multiprocessing import Process
import codecs
import os
import glob
import httplib
import cPickle as pickle

class TransactionLogger(Process):
    """
    This transaction logging process is started seperately from tornado proxy
    This logger checks for *.rd files in cache_dir and then dumps the data
    into db_dir, *.rd files serve as a message that the file corresponding 
    to the hash is ready to be converted.
    """
    def __init__(self, cache_dir, db_dir):
        Process.__init__(self)
        self.cache_dir = cache_dir
        self.db_dir = db_dir
        
    # This function is necessary for writing response codes as W3C strings
    def status_code_to_name(self, response_code):
        try:
            return(httplib.responses[int(response_code)])
        except:
            return("Code Not Known")
    
    # This is the main function which dumps the transactions into
    # human readable form
    def save_to_file(self, dumped_dict, request_hash):
        file_path = os.path.join(self.db_dir, request_hash)
        transaction_file = codecs.open(file_path, 'w', 'UTF-8')
        
        transaction_file.write("="*50 + " HTTP URL " + "="*50 + "\r\n")
        transaction_file.write(dumped_dict['request_url']+'\r\n')
        
        transaction_file.write("="*50 + " HTTP REQUEST " + "="*50 + "\r\n")
        transaction_file.write(dumped_dict['request_method'] + ' ' + dumped_dict['request_url'] +  ' ' + dumped_dict['request_version'] + '\r\n')
        for header, value in dumped_dict['request_headers'].items():
            transaction_file.write("%s: %s\r\n"%(header, value))
            
        transaction_file.write("\r\n")
        if dumped_dict['request_body']:
            transaction_file.write(dumped_dict['request_body'])
            transaction_file.write("\r\n\r\n")
        
        transaction_file.write("="*50 + " HTTP RESPONSE HEADERS" + "="*50 + "\r\n")
        transaction_file.write("%s %s\r\n"%(dumped_dict['response_code'], self.status_code_to_name(dumped_dict['response_code'])))
        for header, value in dumped_dict['response_headers'].items():
            transaction_file.write("%s: %s\r\n"%(header, value))
            
        transaction_file.write("="*50 + " HTTP RESPONSE BODY" + "="*50 + "\r\n")
        try:
            transaction_file.write(dumped_dict['response_body'])
        except:
            transaction_file.write("Seems Binary")
        
        transaction_file.close()
            
            
    def run(self):
        try:
            while True:
                for file_path in glob.glob(os.path.join(self.cache_dir, "*.rd")):
                    dumped_dict = pickle.load(open(file_path[:-3], 'rb'))
                    self.save_to_file(dumped_dict, file_path.split('/')[-1][:-3])
                    os.remove(file_path)
        except:
            for file_path in glob.glob(os.path.join(self.cache_dir, "*.rd")):
                dumped_dict = pickle.load(open(file_path[:-3], 'rb'))
                self.save_to_file(dumped_dict, file_path.split('/')[-1][:-3])
                os.remove(file_path)
