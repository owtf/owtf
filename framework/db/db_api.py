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
APIs used for DB
'''
from collections import defaultdict
from framework.lib import *
import os
import time

function_list = defaultdict(list)
#lists of functions for push and pull with expected number of arguments
function_list['push']= {'Add':{3},'ModifyRecord':{4},'IncreaseSync':{2},'CalcSync':{2},'LoadDB':{2},'SaveDB':{2}
        ,'SaveDBs':{0},'SaveDBLine':{3},'AddError':{1}}
function_list['pull'] = {'GetPath':{1},'Get':{2},'GetData':{2},'GetRecord':{3},'GetRecordAsMatch':{2},
                 'Search':{4},'GetSyncCount':{2},'GetLength':{2},'IsEmpty':{2},'GetDBNames':{0},'GetNextHTMLID':{0}
                 ,'ErrorCount':{0},'ErrorData':{0},'GetSeed':{0}}

    #check if function is valid or not
def is_valid(function_name,arguments,response_type):
#check if function name is there in list corresponding to response type
#if yes then check if number of arguments are expected in numbers
    if(function_name in function_list[response_type]):
        num_args = len(arguments)
        if(num_args in function_list[response_type].get(function_name)):
            return True
    return False
    
    
    #initializes all the queues directories for messagin system     
