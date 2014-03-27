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

The DB stores HTTP transactions, unique URLs and more. 
'''
from jinja2 import Environment, PackageLoader, Template
from sqlalchemy import desc, asc
from collections import defaultdict
from framework.http import transaction
from framework.db import models
from framework.lib.general import *
import os
import json
import re
import logging

# Transaction DB field order:
# LogID, LogTime, LogTimeHuman, LogStatus, LogMethod, LogURL, LogData
TLOG_ID = 0
TLOG_SCOPE = 1 
TLOG_TIME = 2 
TLOG_TIMEHUMAN = 3
TLOG_STATUS = 4 
TLOG_METHOD = 5 
TLOG_URL = 6 
TLOG_DATA = 7 

NAME_TO_OFFSET = { 'ID' : TLOG_ID, 'Scope' : TLOG_SCOPE, 'Time' : TLOG_TIME, 'TimeHuman' : TLOG_TIMEHUMAN, 'Status' : TLOG_STATUS, 'Method' : TLOG_METHOD, 'URL' : TLOG_URL, 'Data' : TLOG_DATA }

REGEX_TYPES = ['headers', 'body']

class TransactionManager(object):
        def __init__(self, Core):
                self.Core = Core # Need access to reporter for pretty html trasaction log
                self.regexs = defaultdict(list)
                for regex_type in REGEX_TYPES:
                    self.regexs[regex_type] = {}
                self.CompileRegexs()

        def NumTransactions(self, Scope = True): # Return num transactions in scope by default
                Session = self.Core.DB.Target.GetTransactionDBSession()
                session = Session()
                count = session.query(models.Transaction).filter(Scope).count()
                session.close()
                return(count)

        def SetRandomSeed(self, RandomSeed):
                self.RandomSeed = RandomSeed
                self.DefineTransactionBoundaries( ['HTTP URL', 'HTTP Request', 'HTTP Response Headers', 'HTTP Response Body'] )

        def DefineTransactionBoundaries(self, BoundaryList):# Defines the full HTTP transaction formatting (important 4 parsing)
                self.Padding = "="*50
                Boundaries = []
                for BoundaryName in BoundaryList:
                        Boundaries.append(self.Padding+" "+BoundaryName+" "+self.Padding+self.RandomSeed+"\n")
                self.TBoundaryURL, self.TBoundaryReq, self.TBoundaryResHeaders, self.TBoundaryResBody = Boundaries

        def IsTransactionAlreadyAdded(self, Criteria, target = None):
            return(len(self.GetAll(Criteria, target)) > 0)

        def GetFirst(self, Criteria, target = None): # Assemble only the first transaction that matches the criteria from DB
            Session = self.Core.DB.Target.GetTransactionDBSession(target)
            session = Session()
            query = session.query(models.Transaction)
            if 'URL' in Criteria.keys():
                query = self.FilterByURL(query, Criteria['URL'])
            if 'Method' in Criteria.keys():
                query = self.FilterByMethod(query, Criteria['Method'])
            if 'Data' in Criteria.keys():
                query = self.FilterByData(query, Criteria['Data'])
            return(self.DeriveTransaction(query.first()))

        def GetAll(self, Criteria, target = None): # Assemble ALL transactions that match the criteria from DB
            Session = self.Core.DB.Target.GetTransactionDBSession(target)
            session = Session()
            query = session.query(models.Transaction)
            if 'URL' in Criteria.keys():
                query = self.FilterByURL(query, Criteria['URL'])
            if 'Method' in Criteria.keys():
                query = self.FilterByMethod(query, Criteria['Method'])
            if 'Data' in Criteria.keys():
                query = self.FilterByData(query, Criteria['Data'])
            return(self.DeriveTransactions(query.all()))

        def DeriveTransaction(self, t):
            if t:
                owtf_transaction = transaction.HTTP_Transaction(None)
                response_body = t.response_body
                if t.response_binary:
                    response_body = str(response_body)
                grep_output = None
                if t.grep_output:
                    grep_output = json.loads(t.grep_output)
                owtf_transaction.SetTransactionFromDB(
                                                        t.url,
                                                        t.method,
                                                        t.status,
                                                        str(t.time),
                                                        t.time_human,
                                                        t.request_data,
                                                        t.raw_request,
                                                        t.response_headers,
                                                        response_body,
                                                        grep_output
                                                     )
                return owtf_transaction
            return(None)

        def DeriveTransactions(self, transactions):
            owtf_tlist = []
            for transaction in transactions:
                owtf_tlist.append(self.SetTransaction(transaction))
            return(owtf_tlist)

        def FilterByURL(self, query, url):
            return query.filter_by(url = url)

        def FilterByMethod(self, query, method):
            return query.filter_by(method = method)

        def FilterByData(self, query, data):
            return query.filter_by(data = data)

        def LogTransaction(self, transaction, target = None):
            Session = self.Core.DB.Target.GetTransactionDBSession(target)
            session = Session()
            urls_list = []
            # TODO: This shit will go crazy on non-ascii characters
            try:
                unicode(transaction.GetRawResponseBody(), "utf-8")
                response_body = transaction.GetRawResponseBody()
                is_binary = False
                grep_output = json.dumps(self.GrepTransaction(transaction))
            except UnicodeDecodeError:
                response_body = buffer(transaction.GetRawResponseBody())
                is_binary = True
                grep_output = None
            finally:
                session.add(models.Transaction( url = transaction.URL,
                                                scope = transaction.InScope(),
                                                method = transaction.Method,
                                                data = transaction.Data,
                                                time = float(transaction.Time),
                                                time_human = transaction.TimeHuman,
                                                raw_request = transaction.GetRawRequest(),
                                                response_status = transaction.GetStatus(False),
                                                response_headers = transaction.GetResponseHeaders(),
                                                response_body = response_body,
                                                response_binary = is_binary,
                                                grep_output = grep_output
                                              ))
            urls_list.append([transaction.URL, True, transaction.InScope()])
            session.commit()
            session.close()

        def LogTransactions(self, transaction_list, target = None):
            Session = self.Core.DB.Target.GetTransactionDBSession(target)
            session = Session()
            urls_list = []
            for transaction in transaction_list:
                # TODO: This shit will go crazy on non-ascii characters
                #try:
                unicode(transaction.GetRawResponseBody(), "utf-8")
                response_body = transaction.GetRawResponseBody()
                is_binary = False
                grep_output = json.dumps(self.GrepTransaction(transaction))
                """
                except UnicodeDecodeError:
                    response_body = buffer(transaction.GetRawResponseBody())
                    is_binary = True
                    grep_output = None
                finally:
                """
                session.add(models.Transaction( url = transaction.URL,
                                                scope = transaction.InScope(),
                                                method = transaction.Method,
                                                data = transaction.Data,
                                                time = float(transaction.Time),
                                                time_human = transaction.TimeHuman,
                                                raw_request = transaction.GetRawRequest(),
                                                response_status = transaction.GetStatus(),
                                                response_headers = transaction.GetResponseHeaders(),
                                                response_body = response_body,
                                                response_binary = is_binary,
                                                grep_output = grep_output
                                              ))
                urls_list.append([transaction.URL, True, transaction.InScope()])
            session.commit()
            session.close()
            self.Core.DB.URL.ImportProcessedURLs(urls_list)
                                                
        def LogTransactionsFromLogger(self, transactions_dict):
            for target, transaction_list in transactions_dict.items():
                if transaction_list:
                    self.LogTransactions(transaction_list, target)

        def GetNumTransactionsInScope(self):
            return self.NumTransactions()

        def GetByID(self, ID):
            Session = self.Core.DB.Target.GetTransactionDBSession()
            session = Session()
            model_obj = session.query(models.Transaction).get(id = ID)
            if model_obj:
                return(self.DeriveTransaction(model_obj))
            return(model_obj) # None returned if no such transaction

        def GetTopTransactionIDsBySpeed(self, Num = 10, Order = "Asc"):
            Session = self.Core.DB.Target.GetTransactionDBSession()
            session = Session()
            if Order == "Desc":
                results = session.query(models.Transaction.id).order_by(desc(models.Transaction.time)).limit(Num)
            else:
                results = session.query(models.Transaction.id).order_by(asc(models.Transaction.time)).limit(Num)
            session.close()
            results = [i[0] for i in results]
            return(results) # Return list of matched IDs

        def CompileHeaderRegex(self, header_list):
            return(re.compile('('+'|'.join(header_list)+'): ([^\r]*)', re.IGNORECASE))

        def CompileResponseRegex(self, regexp):
            return(re.compile(regexp, re.IGNORECASE | re.DOTALL))

        def CompileRegexs(self):
            for key in self.Core.Config.GetReplacementDict().keys():
                key = key[3:-3] # Remove "@@@"
                if key.startswith('HEADERS'):
                    header_list = self.Core.Config.GetHeaderList(key)
                    self.regexs['headers'][key] = self.CompileHeaderRegex(header_list)
                elif key.startswith('RESPONSE'):
                    RegexpName, GrepRegexp, PythonRegexp = self.Core.Config.FrameworkConfigGet(key).split('_____')
                    self.regexs['body'][key] = self.CompileResponseRegex(PythonRegexp)

        def GrepTransaction(self, owtf_transaction):
            grep_output = []
            for regex_name, regex in self.regexs['headers'].items():
                grep_output += self.GrepResponseHeaders(regex_name, regex, owtf_transaction)
            for regex_name in self.regexs['body'].items():
                grep_output += self.GrepResponseBody(regex_name, regex, owtf_transaction)
            return(grep_output)

        def GrepResponseBody(self, regex_name, regex, owtf_transaction):
            return(self.Grep(regex_name, regex, owtf_transaction.GetRawResponseBody()))

        def GrepResponseHeaders(self, regex_name, regex, owtf_transaction):
            return(self.Grep(regex_name, regex, owtf_transaction.GetResponseHeaders()))

        def Grep(self, regex_name, regex, data):
            results = regex.findall(data)
            if results:
                return([{regex_name: results}])
            return([])
