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

The DB stores HTTP transactions, unique URLs and more.

"""

import os
import re
import json
import base64
import logging

from sqlalchemy import desc, asc
from collections import defaultdict

from framework.lib.exceptions import InvalidTransactionReference, \
                                     InvalidParameterType
from framework.http import transaction
from framework.db import models


REGEX_TYPES = ['HEADERS', 'BODY'] # The regex find differs for these types :P


class TransactionManager(object):
    def __init__(self, Core):
        self.Core = Core # Need access to reporter for pretty html trasaction log
        self.regexs = defaultdict(list)
        for regex_type in REGEX_TYPES:
            self.regexs[regex_type] = {}
        self.CompileRegexs()

    def NumTransactions(self, Scope = True, target_id = None): # Return num transactions in scope by default
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        count = session.query(models.Transaction).filter_by(scope = Scope).count()
        session.close()
        return(count)

    def IsTransactionAlreadyAdded(self, Criteria, target_id = None):
        return(len(self.GetAll(Criteria, target_id)) > 0)

    def GenerateQueryUsingSession(self, session, Criteria):
        query = session.query(models.Transaction)
        if Criteria.get('url', None):
            if isinstance(Criteria.get('url'), (str, unicode)):
                query = query.filter_by(url = Criteria['url'])
            if isinstance(Criteria.get('url'), list):
                query = query.filter(models.Transaction.url.in_(Criteria.get('url')))
        if Criteria.get('method', None):
            if isinstance(Criteria.get('method'), (str, unicode)):
                query = query.filter_by(method = Criteria['method'])
            if isinstance(Criteria.get('method'), list):
                query = query.filter(models.Transaction.method.in_(Criteria.get('method')))
        if Criteria.get('data', None):
            if isinstance(Criteria.get('data'), (str, unicode)):
                query = query.filter_by(data = Criteria['data'])
            if isinstance(Criteria.get('data'), list):
                query = query.filter(models.Transaction.data.in_(Criteria.get('data')))
        if Criteria.get('scope', None):
            if isinstance(Criteria.get('scope'), list):
                Criteria['scope'] = Criteria['scope'][0]
            query = query.filter_by(scope = self.Core.Config.ConvertStrToBool(Criteria['scope']))
        try:
            if Criteria.get('id[lt]', None):
                if isinstance(Criteria.get('id[lt]'), list):
                    Criteria['id[lt]'] = Criteria['id[lt]'][0]
                query = query.filter(models.Transaction.id < int(Criteria['id[lt]']))
            if Criteria.get('id[gt]', None):
                if isinstance(Criteria.get('id[gt]'), list):
                    Criteria['id[gt]'] = Criteria['id[gt]'][0]
                query = query.filter(models.Transaction.id > int(Criteria['id[gt]']))
        except ValueError:
            raise InvalidParameterType("Invalid parameter type for transaction db for id[lt] or id[gt]")
        return(query)

    def GetFirst(self, Criteria, target_id = None): # Assemble only the first transaction that matches the criteria from DB
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        query = self.GenerateQueryUsingSession(session, Criteria)
        return(self.DeriveTransaction(query.first()))

    def GetAll(self, Criteria, target_id = None): # Assemble ALL transactions that match the criteria from DB
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        query = self.GenerateQueryUsingSession(session, Criteria)
        return(self.DeriveTransactions(query.all()))

    def DeriveTransaction(self, t):
        if t:
            owtf_transaction = transaction.HTTP_Transaction(None)
            response_body = t.response_body
            if t.binary_response:
                response_body = base64.b64decode(response_body)
            grep_output = None
            if t.grep_output:
                grep_output = json.loads(t.grep_output)
            owtf_transaction.SetTransactionFromDB(
                                                    t.id,
                                                    t.url,
                                                    t.method,
                                                    t.response_status,
                                                    str(t.time),
                                                    t.time_human,
                                                    t.data,
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
            owtf_tlist.append(self.DeriveTransaction(transaction))
        return(owtf_tlist)

    def GetTransactionModel(self, transaction):
        try:
            response_body = unicode(transaction.GetRawResponseBody(), "utf-8")
            binary_response = False
            grep_output = json.dumps(self.GrepTransaction(transaction)) if transaction.InScope() else None
        except UnicodeDecodeError:
            response_body = base64.b64encode(transaction.GetRawResponseBody())
            binary_response = True
            grep_output = None
        finally:
            return(models.Transaction( url = transaction.URL,
                                            scope = transaction.InScope(),
                                            method = transaction.Method,
                                            data = transaction.Data,
                                            time = float(transaction.Time),
                                            time_human = transaction.TimeHuman,
                                            raw_request = transaction.GetRawRequest(),
                                            response_status = transaction.GetStatus(),
                                            response_headers = transaction.GetResponseHeaders(),
                                            response_body = response_body,
                                            binary_response = binary_response,
                                            grep_output = grep_output
                                          ))

    def LogTransaction(self, transaction, target_id = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        urls_list = []
        # TODO: This shit will go crazy on non-ascii characters
        session.merge(self.GetTransactionModel(transaction))
        urls_list.append([transaction.URL, True, transaction.InScope()])
        session.commit()
        session.close()
        self.Core.DB.URL.ImportProcessedURLs(urls_list)

    def LogTransactions(self, transaction_list, target_id = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        urls_list = []
        for transaction in transaction_list:
            # TODO: This shit will go crazy on non-ascii characters
            session.merge(self.GetTransactionModel(transaction))
            urls_list.append([transaction.URL, True, transaction.InScope()])
        session.commit()
        session.close()
        self.Core.DB.URL.ImportProcessedURLs(urls_list, target_id)

    def LogTransactionsFromLogger(self, transactions_dict):
        # transaction_dict is a dictionary with target_id as key and list of owtf transactions
        for target_id, transaction_list in transactions_dict.items():
            if transaction_list:
                self.LogTransactions(transaction_list, target_id)

    def DeleteTransaction(self, transaction_id, target_id = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        session.delete(session.query(models.Transaction).get(transaction_id))
        session.commit()
        session.close()

    def GetNumTransactionsInScope(self, target_id = None):
        return self.NumTransactions(target_id = target_id)

    def GetByID(self, ID, target_id = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        model_obj = session.query(models.Transaction).get(ID)
        session.close()
        if model_obj:
            return(self.DeriveTransaction(model_obj))
        return(model_obj) # None returned if no such transaction

    def GetByIDs(self, id_list, target_id = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        model_objs = []
        for ID in id_list:
            model_obj = session.query(models.Transaction).get(ID)
            if model_obj:
                model_objs.append(model_obj)
        session.close()
        return(self.DeriveTransactions(model_objs))

    def GetTopTransactionsBySpeed(self, Order = "Desc", Num = 10):
        Session = self.Core.DB.Target.GetTransactionDBSession()
        session = Session()
        if Order == "Desc":
            results = session.query(models.Transaction).order_by(desc(models.Transaction.time)).limit(Num)
        else:
            results = session.query(models.Transaction).order_by(asc(models.Transaction.time)).limit(Num)
        session.close()
        return(self.DeriveTransactions(results))

    def CompileHeaderRegex(self, header_list):
        return(re.compile('('+'|'.join(header_list)+'): ([^\r]*)', re.IGNORECASE))

    def CompileResponseRegex(self, regexp):
        return(re.compile(regexp, re.IGNORECASE | re.DOTALL))

    def CompileRegexs(self):
        for key in self.Core.Config.GetFrameworkConfigDict().keys():
            key = key[3:-3] # Remove "@@@"
            if key.startswith('HEADERS'):
                header_list = self.Core.Config.GetHeaderList(key)
                self.regexs['HEADERS'][key] = self.CompileHeaderRegex(header_list)
            elif key.startswith('RESPONSE'):
                RegexpName, GrepRegexp, PythonRegexp = self.Core.Config.FrameworkConfigGet(key).split('_____')
                self.regexs['BODY'][key] = self.CompileResponseRegex(PythonRegexp)

    def GrepTransaction(self, owtf_transaction):
        grep_output = {}
        for regex_name, regex in self.regexs['HEADERS'].items():
            grep_output.update(self.GrepResponseHeaders(regex_name, regex, owtf_transaction))
        for regex_name, regex in self.regexs['BODY'].items():
            grep_output.update(self.GrepResponseBody(regex_name, regex, owtf_transaction))
        return(grep_output)

    def GrepResponseBody(self, regex_name, regex, owtf_transaction):
        return(self.Grep(regex_name, regex, owtf_transaction.GetRawResponseBody()))

    def GrepResponseHeaders(self, regex_name, regex, owtf_transaction):
        return(self.Grep(regex_name, regex, owtf_transaction.GetResponseHeaders()))

    def Grep(self, regex_name, regex, data):
        results = regex.findall(data)
        output = {}
        if results:
            output.update({regex_name: results})
        return(output)

    def SearchByRegexName(self, regex_name, target = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target)
        session = Session()
        transaction_models = session.query(models.Transaction).filter(models.Transaction.grep_output.like("%"+regex_name+"%")).all()
        num_transactions_in_scope = session.query(models.Transaction).filter_by(scope = True).count()
        session.close()
        return([regex_name, self.DeriveTransactions(transaction_models), num_transactions_in_scope])

    def SearchByRegexNames(self, name_list, target = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target)
        session = Session()
        results = []
        for regex_name in name_list:
            transaction_models = session.query(models.Transaction).filter(models.Transaction.grep_output.like("%"+regex_name+"%")).all()
            num_transactions_in_scope = session.query(models.Transaction).filter_by(scope = True).count()
            results.append([regex_name, self.DeriveTransactions(transaction_models), num_transactions_in_scope])
        session.close()
        return(results)

#-------------------------------------------------- API Methods --------------------------------------------------
    def DeriveTransactionDict(self, tdb_obj, include_raw_data = False):
        tdict = dict(tdb_obj.__dict__)  # Create a new copy so no accidental changes
        tdict.pop("_sa_instance_state")
        tdict.pop("grep_output")  # grep_output only required by OWTF and not for any API user
        if not include_raw_data:
            tdict.pop("raw_request", None)
            tdict.pop("response_headers", None)
            tdict.pop("response_body", None)
        else:
            if tdict["binary_response"]:
                tdict["response_body"] = base64.b64encode(str(tdict["response_body"]))
        return tdict

    def DeriveTransactionDicts(self, tdb_obj_list, include_raw_data = False):
        dict_list = []
        for tdb_obj in tdb_obj_list:
            dict_list.append(self.DeriveTransactionDict(tdb_obj, include_raw_data))
        return dict_list

    def GetAllAsDicts(self, Criteria, target_id = None, include_raw_data = False): # Assemble ALL transactions that match the criteria from DB
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        query = self.GenerateQueryUsingSession(session, Criteria)
        transaction_objs = query.all()
        session.close()
        return(self.DeriveTransactionDicts(transaction_objs, include_raw_data))

    def GetByIDAsDict(self, trans_id, target_id = None):
        Session = self.Core.DB.Target.GetTransactionDBSession(target_id)
        session = Session()
        transaction_obj = session.query(models.Transaction).get(trans_id)
        session.close()
        if not transaction_obj:
            raise InvalidTransactionReference("No transaction with " + str(trans_id) + " exists for target with id " + str(target_id) if target_id else self.Core.DB.Target.GetTargetID())
        return self.DeriveTransactionDict(transaction_obj, include_raw_data = True)
