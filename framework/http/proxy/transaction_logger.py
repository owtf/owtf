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
from framework.http import transaction
from framework.http.proxy.cache_handler import response_from_cache, request_from_cache
from framework import timer
import os
import glob
import time

class TransactionLogger(Process):
    """
    This transaction logging process is started seperately from tornado proxy
    This logger checks for *.rd files in cache_dir and saves it as owtf db
    transaction, *.rd files serve as a message that the file corresponding 
    to the hash is ready to be converted.
    """
    def __init__(self, coreobj):
        Process.__init__(self)
        self.Core = coreobj
        self.cache_dir = self.Core.Config.Get('CACHE_DIR')

    def get_target_for_transaction(self, request, response):
        for Target in self.Core.Config.GetTargets():
            if request.url.startswith(Target):
                return Target
            else:
                try:
                    if response.headers["Referer"].startswith(Target):
                        return Target
                except KeyError:
                    pass
        return self.Core.Config.GetTarget()

    def add_owtf_transaction(self, request_hash):
        owtf_transaction = transaction.HTTP_Transaction(timer.Timer())
        request = request_from_cache(request_hash, self.cache_dir)
        response = response_from_cache(request_hash, self.cache_dir)
        request.in_scope = self.Core.IsInScopeURL(request.url)
        owtf_transaction.ImportProxyRequestResponse(request, response)
        owtf_transaction.Target = self.get_target_for_transaction(request, response)
        self.Core.DB.Transaction.LogTransaction(owtf_transaction)
        
    def run(self):
        try:
            while True:
                if glob.glob(os.path.join(self.cache_dir, "url", "*.rd")):
                    for file_path in glob.glob(os.path.join(self.cache_dir, "url", "*.rd")):
                        request_hash = os.path.basename(file_path)[:-3]
                        self.add_owtf_transaction(request_hash)
                        os.remove(file_path)
                else:
                    time.sleep(2)

        except KeyboardInterrupt:
            for file_path in glob.glob(os.path.join(self.cache_dir, "url", "*.rd")):
                request_hash = os.path.basename(file_path)[:-3]
                self.add_owtf__transaction(request_hash)
                os.remove(file_path)
        finally:
            exit()
