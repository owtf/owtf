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

This File is for server who will entertain pull requests
'''
from collections import defaultdict
from framework.lib import *
from framework.lib.general import log
import os
import random
import time

class pull_server:
    
    def __init__(self,Core):
        self.Core = Core
        
    
    def handle_request(self,callback_function,queue,queue_name="pull"):
        #pull server to handle the pull requests, It returns the response by making file of same name in 
        #request and response folder
        request_dir = general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name]
        response_dir = general.OUTGOING_QUEUE_TO_DIR_MAPPING[queue_name]
        
        delay = 0.025
                    #wait for request directory to exist in starting
        general.wait_until_dir_exists(request_dir,delay)
        
        while True:
            if queue.empty()==False:
                break
            try:
                files = general.get_files(request_dir)
                #while we have files for procesing
                while len(files)>0:
                    #open('file1','w+').write(str(files))
                    for full_filename in files:
                        filen = full_filename.split("/")
                        filename = filen[len(filen)-1]
                        #skip lock files
                        if ".lock" in filename:
                            continue
                        #skip_if_locked is True then file is skipped if it is locked    
                        self.Core.Timer.StartTimer('read')
                        data = general.atomic_read_from_file(request_dir, filename, skip_if_locked=True)
                        log("pull server "+filename[0:3]+"    "+self.Core.Timer.GetElapsedTimeAsStr('read'),0)
                        if data:
                            
                            result = callback_function(data,"pull")
                            #write result to response directory
                            general.atomic_write_to_file(response_dir, filename, result)
                            #remove the processed file
                            os.remove(os.path.join(request_dir,filename))
                    files = general.get_files(request_dir)
                #give away cpu
                self.Core.Timer.StartTimer('sleep')
                time.sleep(delay)
                log("pull server after sleeping "+self.Core.Timer.GetElapsedTimeAsStr('sleep'),0)
            except KeyboardInterrupt:
                break
            except Exception,e:
                log("Unexpected Pull server error: "+str(e))
                break
                   