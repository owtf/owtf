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

Client to connect with messaging and DB
'''
from collections import defaultdict
from framework.db import db_api
from framework.lib import *
from framework.lib.messaging import pull_client
from framework.lib.messaging import push_client
import json
import os
import time
from framework.lib.general import CallMethod

class db_client:
    
    def __init__(self, Core):
        self.Core = Core 
        self.dbapi = db_api.db_api(Core)
        self.push = push_client.push_client(Core)
        self.pull = pull_client.pull_client(Core)

    #this functions sends request to messaging system depending on what is response type(push or pull)
    def db_send(self,argumentlist,request_type):
        if request_type=='push':
            #if it is a push simply push the arguments
            self.push.push_msg(json.dumps(argumentlist))
        else:
            #if it is pull request we have to return the result
            result = self.pull.pull_msg(json.dumps(argumentlist))
            if result:
                return json.loads(result)
            return result
    
    #callback function which calls DB functions and is invoked by messaging server
    def db_callback_function(self,data,response_type):
        message = json.loads(data)
        function = message['function']
        args = message['arguments']
        #checks if function is valid or not
        if(self.dbapi.is_valid(function, args, response_type)):
            
            result = CallMethod(self.Core.DB.DBHandler, function, args)
            return json.dumps(result)