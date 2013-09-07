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

This File is for server who will entertain push requests
'''
from collections import defaultdict
from framework.lib import *
import os
import random
import time


def handle_request(callback_function,queue,queue_name="push"):
        #push server to handle the push requests
    request_dir = general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name]
        
        
    general.wait_until_dir_exists(request_dir,general.sleep_delay)
    while True:
        if queue.empty()==False:
            break
        try:
            files = general.get_files(request_dir)
            #while we have files for procesing
            while len(files)>0:
                for full_filename in files:
                    filen = full_filename.split("/")
                    filename = filen[len(filen)-1]
                    #skip lock files
                    if ".lock" in filename:
                        continue
                    #skip_if_locked is True then file is skipped if it is locked
                    data = general.atomic_read_from_file(request_dir, filename, skip_if_locked=True)
                    if data:
                        callback_function(data,"push")
                            #remove the processed file
                        os.remove(os.path.join(request_dir,filename))
                files = general.get_files(request_dir)
                #give away cpu
            time.sleep(general.sleep_delay)
        except KeyboardInterrupt:
            break
        except Exception,e:
            general.log("Unexpected Push server error: "+str(e))
            break
                   