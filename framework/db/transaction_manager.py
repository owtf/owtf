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
import re,logging

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

class TransactionManager(object):
        def __init__(self, Core):
                self.Core = Core # Need access to reporter for pretty html trasaction log

        def Search(self, Criteria):
                if 'Method' in Criteria: # Ensure a valid HTTP Method is used instead of "" when the Method is specified in the Criteria
                        Criteria['Method'] = DeriveHTTPMethod(Criteria['Method'], GetDictValueOrBlank(Criteria, 'Data'))
                Session = self.Core.DB.Target.GetTransactionDBSession()
                return self.Core.DB.SearchTransactionDB(Criteria)

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

        def GetFirst(self, Criteria): # Assemble only the first transaction that matches the criteria from DB
                MatchList = self.Search( Criteria )
                if len(MatchList) > 0:
                        return self.GetByID(MatchList[0]['ID'])
                return False

        def GetAll(self, Criteria): # Assemble ALL transactions that match the criteria from DB
                Transactions = []
                MatchList = self.Search( Criteria )
                if len(MatchList) > 0:
                        for Item in MatchList:
                                Transactions.append(self.GetByID(Item['ID']))
                return Transactions

        def IsTransactionAlreadyAdded(self, Criteria): # To avoid requests already made
                Result = len(self.Search( Criteria )) > 0
                log(str(Criteria)+" in DB: "+str(Result))
                return Result

        def LogTransaction(self, Transaction):# The Transaction Obj will be modified here with a new Transaction ID and HTML Link to it
                self.Core.Config.SetTarget(Transaction.Target) # Attr set in transaction_logger
                self.Core.DB.URL.AddURL(Transaction.URL, Transaction.Found) # Log Transaction URL in URL DB (this also classifies the URL: scope, external, file, etc)
                #Need to log all transactions, even from out of scope resources, this is the simplest and most flexible approach (no log duplication, etc)
                ID = self.SaveTransactionTXTIndex(Transaction) # Update TXT Index and get ID for Transaction
                TransacPath, ReqPath, ResHeadersPath, ResBodyPath = self.SaveTransactionFiles(ID, Transaction)# Store files in disk
                self.SaveTransactionHTMLIndex(ID, Transaction, TransacPath, ReqPath, ResHeadersPath, ResBodyPath)# Build links 2 files,etc 

        def LogTransactions(self, transaction_list, target = None):
            Session = self.Core.DB.Target.GetTransactionDBSession(target)
            session = Session()
            for transaction in transaction_list:
                session.add(models.Transaction( url = transaction.URL,
                                                scope = transaction.InScope(),
                                                method = transaction.Method,
                                                data = transaction.Data,
                                                time = int(transaction.Time),
                                                time_human = transaction.TimeHuman,
                                                raw_request = transaction.GetRawRequest(),
                                                request_body = transaction.GetRawResponseBody(),
                                                response_status = transaction.GetStatus(False),
                                                response_headers = transaction.GetResponseHeaders(),
                                                response_body = transaction.GetRawResponseBody()
                                              ))
            session.commit()
            session.close()
                                                
        def LogTransactionsFromLogger(self, transactions_dict):
            for target, transaction_list in transactions_dict:
                if transaction_list:
                    self.LogTransactions(transaction_list, target)

        def GetNumTransactionsInScope(self):
                return self.NumTransactions()

        def AssembleTransactionForDB(self, Transaction): # Turns an HTTP Transaction into a Parseable text file:
                return self.TBoundaryURL + Transaction.URL+"\n" + self.TBoundaryReq + Transaction.GetRawRequest() + self.TBoundaryResHeaders + Transaction.GetRawResponseHeaders() + self.TBoundaryResBody + Transaction.GetRawResponseBody()

        def GetByID(self, ID):
                MatchList = self.Search( { 'ID' : ID } )
                if len(MatchList) > 0: # Transaction found
                        T = MatchList[0]
                        Transaction = transaction.HTTP_Transaction(self.Core.Timer)
                        TStr = ""
                        Prefix = self.GetPrefix(T['Scope'])
                        try:
                                Path = self.Core.Config.Get('TRANSACTION_LOG_TRANSACTIONS')+Prefix+T['ID']+".txt"
                                TStr = open(Path).read() # Try to retrieve transaction to memory
                        except IOError:
                                self.Core.Error.Add("ERROR: Transaction "+T['ID']+" could not be found, has the DB been tampered with?")
                        if TStr: # Transaction could be read from DB
                                Request, ResponseHeaders, ResponseBody = self.ParseDBTransaction(TStr, T['Status'])
                                Transaction.SetTransactionFromDB(T, Request, ResponseHeaders, ResponseBody)
                                self.SetIDForTransaction(Transaction, T['ID'], Path)
                        return Transaction
                return False # Transaction not found

        def GrepTopTransactionIDsBySpeed(self, Num = 10, Order = "Asc"):
            Session = self.Core.DB.Target.GetTransactionDBSession()
            session = Session()
            if Order == "Desc":
                results = session.query(models.Transaction.id).order_by(desc(models.Transaction.time)).limit(Num)
            else:
                results = session.query(models.Transaction.id).order_by(asc(models.Transaction.time)).limit(Num)
            session.close()
            results = [i[0] for i in results]
            return(results) # Return list of matched IDs

        def GrepTransactionIDsForHeaders(self, HeaderList):
            Regexp = "("+"|".join(HeaderList)+"): "
            Session = self.Core.DB.Target.GetTransactionDBSession()
            session = Session()
            results = session.query(models.Transaction.id).filter(models.Transaction.response_headers.op(Regexp)(REGEX))
            session.close()
            results = [i[0] for i in results]
            return(results) # Return list of matched IDs

        def GrepHeaders(self, HeaderList):
                Regexp = "("+"|".join(HeaderList)+"): "
                return self.GrepForPartialLinks(Regexp, self.Core.Config.Get('TRANSACTION_LOG_RESPONSE_HEADERS')+self.GetScopePrefix()+"*")

        def GrepResponseHeadersRegexp(self, HeadersRegexp):
                GrepLocation = self.Core.Config.Get('TRANSACTION_LOG_RESPONSE_HEADERS')+self.GetScopePrefix()+"*"
                return self.GrepUsingRegexp(HeadersRegexp, GrepLocation)

        def GrepForPartialLinks(self, Regexp, Location): # Returns file: line_match pairs with the file portion ready for partial links
                # Format output to link to link to full transactions:
                #Command = 'grep -HiE "'+Regexp+'" '+Location+" | sed -e 's|"+self.Core.Config.Get('HOST_OUTPUT')+"||g' -e 's|/response_headers/|/|g'"
                Command = 'grep -IHiE "'+Regexp+'" '+Location+" | sed -e 's|"+self.Core.Config.Get('OUTPUT_PATH')+"/||g' -e 's|/"+Location.split('/')[-2]+"/|/|g'"
                return [ Command, self.Core.Shell.shell_exec_monitor(Command) ]

        def GrepForFiles(self, Regexp, Location): # Returns unique filenames that match a search
                # Format output to link to link to full transactions:
                #Command = 'grep -HiE "'+Regexp+'" '+Location+" | sed -e 's|"+self.Core.Config.Get('HOST_OUTPUT')+"||g' -e 's|/response_headers/|/|g'"
                #Not possible: Need to retrieve the files:
                #Command = 'grep -HiE "'+Regexp+'" '+Location+" | cut -f1 -d:|sort -u | sed -e 's|"+self.Core.Config.Get('HOST_OUTPUT')+"||g' -e 's|/"+Location.split('/')[-2]+"/|/|g'"
                Command = 'grep -IHiE "'+Regexp+'" '+Location+" | cut -f1 -d:|sort -u"
                return [ Command, self.Core.Shell.shell_exec_monitor(Command) ]

        def GrepSingleLineResponseRegexp(self, ResponseRegexp): # Single line, 1-pass retrieval
                GrepLocation = self.Core.Config.Get('TRANSACTION_LOG_RESPONSE_BODIES')+self.GetScopePrefix()+"*"
                return self.GrepForPartialLinks(ResponseRegexp, GrepLocation)

        def GrepMultiLineResponseRegexp(self, ResponseRegexp):
                GrepLocation = self.Core.Config.Get('TRANSACTION_LOG_RESPONSE_BODIES')+self.GetScopePrefix()+"*"
                return self.GrepUsingRegexp(ResponseRegexp, GrepLocation)

        def GrepUsingRegexp(self, Regexp, GrepLocation):
                Regexps = Regexp.split('_____')
                if len(Regexps) == 3: # Multi-line, 2-pass retrieval 
                        RegexpName, GrepRegexp, PythonRegexp = Regexps
                        #print "PythonRegexp="+PythonRegexp
                        Regexp = re.compile(PythonRegexp, re.IGNORECASE | re.DOTALL) # Compile before the loop for speed
                        Command, Results = self.GrepForFiles(GrepRegexp, GrepLocation) # Returns response body files that match grep regexp
                        Matches = []
                        for File in Results.split("\n"):
                                if File: # Skip garbage lines = not File
                                        ID = File.split('_')[-1].split('.')[0] # Get Transaction ID from Filename
                                        for FileMatch in Regexp.findall(open(File).read()):
                                                Matches.append( [ ID, FileMatch ] ) # We only need the IDs, All paths retrieved from it
                        return [ Command, RegexpName, Matches ] # Return All matches and the file they were retrieved from
                else: # wtf?
                        raise PluginAbortException("ERROR: Inforrect Configuration setting for Response Regexp: '"+str(Regexp)+"'")
