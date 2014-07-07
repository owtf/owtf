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

This File is for client which has to send a push message
'''
from collections import defaultdict
from framework.lib import *
import os
import time
from framework.lib.general import get_random_str


def push_msg(data,queue_name="push"):
    #Creates a random file inside the /Requests subdirectory within a Queue, 
    #the PushServer will process these files
    file_id = get_random_str(100) + '.msg'
    file_path = os.path.join(general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name], file_id)
    try:
      result = general.atomic_write_to_file(general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name], file_id, data)
      # The following block is important, because of the fact that completion of the operation
      # can be known when the push_server.py removes a processed file :P
      # Without this loop, the normal execution will continue even when db operation is pending.
      # This may lead to some unwanted and cryptic bugs
      while os.path.exists(file_path):
        time.sleep(0.02)
      return result
    except KeyboardInterrupt:
      raise KeyboardInterrupt
