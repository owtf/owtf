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

This File is for client which has to send a pull message
'''
from collections import defaultdict
from framework.lib import *
from framework.lib.general import log, get_random_str
import json
import os
import random

def pull_msg(data,queue_name="pull"):
    #Creates a random file inside the /Requests subdirectory within a Queue, 
    #the PullServer will process these files and then this file will wait for the response as
    #skip_if_locked is false
    file_id = get_random_str(100) + '.msg'
    try:
        general.atomic_write_to_file(general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name], file_id, data)
        result = general.atomic_read_from_file(general.OUTGOING_QUEUE_TO_DIR_MAPPING[queue_name], file_id,False)
        os.remove(general.OUTGOING_QUEUE_TO_DIR_MAPPING[queue_name]+"/"+file_id)
        return result
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    
                   
