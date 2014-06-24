#!/usr/bin/env python
"""

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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Messaging Admin will regulates messaging system.

"""

import multiprocessing
import os
import threading
import time
from collections import defaultdict

from framework.db.db_client import *
from framework.lib import *
from framework.lib.messaging import pull_server, push_server
from framework.lib import io

class message_admin:
    def __init__(self, Core):
        # Need access to reporter for pretty html trasaction log.
        self.Core = Core

    def Init(self):
        """Initializing message admin system."""
        self.InitQueueFiles()
        self.Initthreads()

    def InitQueueFiles(self):
        """Initializes all the queues directories for messagin system."""
        general.INCOMING_QUEUE_TO_DIR_MAPPING = defaultdict(list)
        general.OUTGOING_QUEUE_TO_DIR_MAPPING = defaultdict(list)
        #if /tmp/owtf is not there
        if not os.path.exists(self.Core.Config.Get("MESSAGING_FILE_QUEUE_DIR")):
            io.mkdir(
                self.Core, self.Core.Config.Get("MESSAGING_FILE_QUEUE_DIR"))

        for queue_name in general.QUEUES:
            start_path = self.Core.Config.Get("MESSAGING_FILE_QUEUE_DIR") + queue_name+"/"
            if not os.path.exists(start_path):
                io.mkdir(self.Core, start_path)

            requests_dir = start_path + 'Requests/'
            responses_dir = start_path + 'Responses/'
            if os.path.exists(requests_dir):
                general.removeDirs(requests_dir)
            if os.path.exists(responses_dir):
                general.removeDirs(responses_dir)
            io.mkdir(self.Core, requests_dir)
            io.mkdir(self.Core, responses_dir)
            general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name] = requests_dir
            general.OUTGOING_QUEUE_TO_DIR_MAPPING[queue_name] = responses_dir

    def Initthreads(self):
        """Initializes the two threads for push and pull server."""
        self.pullqueue = multiprocessing.Queue()
        self.pushqueue = multiprocessing.Queue()
        self.dbpull = threading.Thread(target=pull_server.handle_request,args=(self.Core.DB.db_callback_function,self.pullqueue,"pull",))
        self.dbpush = threading.Thread(target=push_server.handle_request,args=(self.Core.DB.db_callback_function,self.pushqueue,"push",))
        self.dbpull.start()
        self.dbpush.start()

    def finishMessaging(self):
        # Delete existing messaging queue files, we have to check only dbpull.
        # If it is there then all other attribues will be there.
        if hasattr(self,'dbpull'):
            #put done in queues and then wait for both  threads to complete
            self.pullqueue.put("done")
            self.pushqueue.put("done")
            self.dbpull.join()
            self.dbpush.join()
            #remove directories
            for queue_name in general.QUEUES:
                #removes all files from the directories(should not be any files ideally
                general.removeDirs(general.INCOMING_QUEUE_TO_DIR_MAPPING[queue_name])
                general.removeDirs(general.OUTGOING_QUEUE_TO_DIR_MAPPING[queue_name])
