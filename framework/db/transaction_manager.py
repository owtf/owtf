#!/usr/bin/env python
"""
The DB stores HTTP transactions, unique URLs and more.
"""

import os
import re
import json
import base64
import logging

from sqlalchemy import desc, asc
from collections import defaultdict
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import TransactionInterface

from framework.db.target_manager import target_required
from framework.lib.exceptions import InvalidTransactionReference, \
                                     InvalidParameterType
from framework.http import transaction
from framework.db import models


# The regex find differs for these types :P
REGEX_TYPES = ['HEADERS', 'BODY']


class TransactionManager(BaseComponent, TransactionInterface):

    COMPONENT_NAME = "transaction"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db = self.get_component("db")
        self.target = self.get_component("target")
        self.url_manager = self.get_component("url_manager")
        self.zest = self.get_component("zest")
        self.regexs = defaultdict(list)
        for regex_type in REGEX_TYPES:
            self.regexs[regex_type] = {}
        self.CompileRegexs()

    @target_required
    def NumTransactions(self, scope=True, target_id=None):
        """Return num transactions in scope by default."""
        count = self.db.session.query(models.Transaction).filter_by(
            scope=scope,
            target_id=target_id).count()
        return(count)

    def IsTransactionAlreadyAdded(self, criteria, target_id=None):
        return(len(self.GetAll(criteria, target_id=target_id)) > 0)

    def GenerateQueryUsingSession(self, criteria, target_id, for_stats=False):
        query = self.db.session.query(models.Transaction).filter_by(
            target_id=target_id)
        # If transaction search is being done
        if criteria.get('search', None):
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), list):
                    criteria['url'] = criteria['url'][0]
                query = query.filter(models.Transaction.url.like(
                    '%' + criteria['url'] + '%'))
            if criteria.get('method', None):
                if isinstance(criteria.get('method'), list):
                    criteria['method'] = criteria['method'][0]
                query = query.filter(models.Transaction.method.like(
                    '%' + criteria.get('method') + '%'))
            if criteria.get('data', None):
                if isinstance(criteria.get('data'), list):
                    criteria['data'] = criteria['data'][0]
                query = query.filter(models.Transaction.data.like(
                    '%' + criteria.get('data') + '%'))
            if criteria.get('raw_request', None):
                if isinstance(criteria.get('raw_request'), list):
                    criteria['raw_request'] = criteria['raw_request'][0]
                query = query.filter(models.Transaction.raw_request.like(
                    '%' + criteria.get('raw_request') + '%'))
            if criteria.get('response_status', None):
                if isinstance(criteria.get('response_status'), list):
                    criteria['response_status'] = criteria['response_status'][0]
                query = query.filter(models.Transaction.response_status.like(
                    '%' + criteria.get('response_status') + '%'))
            if criteria.get('response_headers', None):
                if isinstance(criteria.get('response_headers'), list):
                    criteria['response_headers'] = criteria['response_headers'][0]
                query = query.filter(models.Transaction.response_headers.like(
                    '%' + criteria.get('response_headers') + '%'))
            if criteria.get('response_body', None):
                if isinstance(criteria.get('response_body'), list):
                    criteria['response_body'] = criteria['response_body'][0]
                query = query.filter(
                    models.Transaction.binary_response == False,
                    models.Transaction.response_body.like(
                        '%' + criteria.get('response_body') + '%'))
        else:  # If transaction filter is being done
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), (str, unicode)):
                    query = query.filter_by(url=criteria['url'])
                if isinstance(criteria.get('url'), list):
                    query = query.filter(
                        models.Transaction.url.in_(criteria.get('url')))
            if criteria.get('method', None):
                if isinstance(criteria.get('method'), (str, unicode)):
                    query = query.filter_by(method=criteria['method'])
                if isinstance(criteria.get('method'), list):
                    query = query.filter(
                        models.Transaction.method.in_(criteria.get('method')))
            if criteria.get('data', None):
                if isinstance(criteria.get('data'), (str, unicode)):
                    query = query.filter_by(data=criteria['data'])
                if isinstance(criteria.get('data'), list):
                    query = query.filter(models.Transaction.data.in_(criteria.get('data')))
        # For the following section doesn't matter if filter/search because
        # it doesn't make sense to search in a boolean column :P
        if criteria.get('scope', None):
            if isinstance(criteria.get('scope'), list):
                criteria['scope'] = criteria['scope'][0]
            query = query.filter_by(scope=self.config.ConvertStrToBool(criteria['scope']))
        if criteria.get('binary_response', None):
            if isinstance(criteria.get('binary_response'), list):
                criteria['binary_response'] = criteria['binary_response'][0]
            query = query.filter_by(binary_response=self.config.ConvertStrToBool(criteria['binary_response']))
        if not for_stats:  # query for stats shouldn't have limit and offset
            try:
                query.order_by(models.Transaction.local_timestamp)
                if criteria.get('offset', None):
                    if isinstance(criteria.get('offset'), list):
                        criteria['offset'] = int(criteria['offset'][0])
                    if criteria['offset'] >= 0:
                        query = query.offset(criteria['offset'])
                if criteria.get('limit', None):
                    if isinstance(criteria.get('limit'), list):
                        criteria['limit'] = int(criteria['limit'][0])
                    if criteria['limit'] >= 0:
                        query = query.limit(criteria['limit'])
                else:  # It is too dangerous without a limit argument
                    query.limit(10)  # Default limit value is 10
            except ValueError:
                raise InvalidParameterType(
                    "Invalid parameter type for transaction db")
        return(query)

    @target_required
    def GetFirst(self, Criteria, target_id=None):
        """
        Assemble only the first transaction that matches the criteria from DB
        """
        query = self.GenerateQueryUsingSession(Criteria, target_id)
        return(self.DeriveTransaction(query.first()))

    @target_required
    def GetAll(self, Criteria, target_id=None):
        """
        Assemble ALL transactions that match the criteria from DB
        """
        query = self.GenerateQueryUsingSession(Criteria, target_id)
        return(self.DeriveTransactions(query.all()))

    def DeriveTransaction(self, trans):
        if trans:
            owtf_transaction = transaction.HTTP_Transaction(None)
            response_body = trans.response_body
            if trans.binary_response:
                response_body = base64.b64decode(response_body)
            owtf_transaction.SetTransactionFromDB(
                trans.id,
                trans.url,
                trans.method,
                trans.response_status,
                str(trans.time),
                trans.time_human,
                trans.local_timestamp,
                trans.data,
                trans.raw_request,
                trans.response_headers,
                len(response_body),
                response_body)
            return owtf_transaction
        return (None)

    def DeriveTransactions(self, transactions):
        owtf_tlist = []
        for transaction in transactions:
            owtf_tlist.append(self.DeriveTransaction(transaction))
        return(owtf_tlist)

    def GetTransactionModel(self, transaction):
        try:
            response_body = transaction.GetRawResponseBody().encode("utf-8")
            binary_response = False
        except UnicodeDecodeError:
            response_body = base64.b64encode(transaction.GetRawResponseBody())
            binary_response = True
        finally:
            transaction_model = models.Transaction(
                url=transaction.URL,
                scope=transaction.InScope(),
                method=transaction.Method,
                data=transaction.Data,
                time=float(transaction.Time),
                time_human=transaction.TimeHuman,
                local_timestamp=transaction.LocalTimestamp,
                raw_request=transaction.GetRawRequest(),
                response_status=transaction.GetStatus(),
                response_headers=transaction.GetResponseHeaders(),
                response_body=response_body,
                response_size=len(response_body),
                binary_response=binary_response,
                session_tokens=transaction.GetSessionTokens(),
                login=None,
                logout=None)
            return transaction_model

    @target_required
    def LogTransactions(self, transaction_list, target_id=None):
        """
        This function does the following things in order
        + Add all transactions to a session and commit
        + Add all the grepped results and commit
        + Add all urls to url db
        """
        # Create a usable session
        # Initiate urls_list for holding urls and transaction_model_list
        # for holding transaction models
        urls_list = []
        transaction_model_list = []
        # Add transactions and commit so that we can have access to
        # transaction ids etc..
        for transaction in transaction_list:
            # TODO: This shit will go crazy on non-ascii characters
            transaction_model = self.GetTransactionModel(transaction)
            transaction_model.target_id = target_id
            transaction_model_list.append(transaction_model)
            self.db.session.add(transaction_model)
            urls_list.append([transaction.URL, True, transaction.InScope()])
        self.db.session.commit()
        # Now since we have the ids ready, we can process the grep output and
        # add accordingly. So iterate over transactions and their models.
        for i in range(0, len(transaction_list)):
            # Get the transaction and transaction model from their lists
            owtf_transaction = transaction_list[i]
            transaction_model = transaction_model_list[i]
            # Check if grepping is valid for this transaction
            # For grepping to be valid
            # + Transaction must not have a binary response
            # + Transaction must be in scope
            if (not transaction_model.binary_response) and (transaction_model.scope):
                # Get the grep results
                grep_outputs = self.GrepTransaction(owtf_transaction)
                if grep_outputs:  # If valid grep results exist
                    # Iterate over regex_name and regex results
                    for regex_name, regex_results in grep_outputs.iteritems():
                        # Then iterate over the results to store each result in
                        # a seperate row, but also check to avoid duplicate
                        # entries as we have many-to-many relationship
                        # available for linking
                        for match in regex_results:
                            # Conver the match to json
                            match = json.dumps(match)
                            # Fetch if any existing entry
                            existing_grep_output = self.db.session.query(
                                models.GrepOutput).filter_by(
                                    target_id=target_id,
                                    name=regex_name,
                                    output=match).first()
                            if existing_grep_output:
                                existing_grep_output.transactions.append(
                                    transaction_model)
                                self.db.session.merge(existing_grep_output)
                            else:
                                self.db.session.add(models.GrepOutput(
                                    target_id=target_id,
                                    transactions=[transaction_model],
                                    name=regex_name,
                                    output=match))
        self.db.session.commit()
        zest_trans_list = []
        # Append the transaction in the list if recording is set to on
        if self.zest.IsRecording():
            for model in transaction_model_list:
                zest_trans_list.append(model.id)
            self.zest.addtoRecordedTrans(zest_trans_list)
        self.url_manager.ImportProcessedURLs(urls_list, target_id=target_id)

    def LogTransactionsFromLogger(self, transactions_dict):
        # transaction_dict is a dictionary with target_id as key and list of owtf transactions
        for target_id, transaction_list in transactions_dict.items():
            if transaction_list:
                self.LogTransactions(transaction_list, target_id=target_id)

    @target_required
    def DeleteTransaction(self, transaction_id, target_id=None):
        self.db.session.query(models.Transaction).filter_by(
            target_id=target_id,
            id=transaction_id).delete()
        self.db.session.commit()

    @target_required
    def GetNumTransactionsInScope(self, target_id=None):
        return self.NumTransactions(target_id=target_id)

    def GetByID(self, ID):
        model_obj = None
        try:
            ID = int(ID)
            model_obj = self.db.session.query(models.Transaction).get(ID)
        except ValueError:
            pass
        finally:
            return(model_obj)  # None returned if no such transaction.

    def GetByIDs(self, id_list):
        model_objs = []
        for ID in id_list:
            model_obj = self.GetByID(ID)
            if model_obj:
                model_objs.append(model_obj)
        return(self.DeriveTransactions(model_objs))

    @target_required
    def GetTopTransactionsBySpeed(self, Order="Desc", Num=10, target_id=None):
        if Order == "Desc":
            results = self.db.session.query(models.Transaction).filter_by(
                target_id=target_id).order_by(desc(models.Transaction.time)).limit(Num)
        else:
            results = self.db.session.query(models.Transaction).filter_by(
                target_id=target_id).order_by(asc(models.Transaction.time)).limit(Num)
        return (self.DeriveTransactions(results))

    def CompileHeaderRegex(self, header_list):
        return (re.compile('(' + '|'.join(header_list) + '): ([^\r]*)', re.IGNORECASE))

    def CompileResponseRegex(self, regexp):
        return (re.compile(regexp, re.IGNORECASE | re.DOTALL))

    def CompileRegexs(self):
        for key in self.config.GetFrameworkConfigDict().keys():
            key = key[3:-3]  # Remove "@@@"
            if key.startswith('HEADERS'):
                header_list = self.config.GetHeaderList(key)
                self.regexs['HEADERS'][key] = self.CompileHeaderRegex(header_list)
            elif key.startswith('RESPONSE'):
                RegexpName, GrepRegexp, PythonRegexp = self.config.FrameworkConfigGet(key).split('_____')
                self.regexs['BODY'][key] = self.CompileResponseRegex(PythonRegexp)

    def GrepTransaction(self, owtf_transaction):
        grep_output = {}
        for regex_name, regex in self.regexs['HEADERS'].items():
            grep_output.update(
                self.GrepResponseHeaders(regex_name, regex, owtf_transaction))
        for regex_name, regex in self.regexs['BODY'].items():
            grep_output.update(
                self.GrepResponseBody(regex_name, regex, owtf_transaction))
        return (grep_output)

    def GrepResponseBody(self, regex_name, regex, owtf_transaction):
        return (self.Grep(regex_name, regex, owtf_transaction.GetRawResponseBody()))

    def GrepResponseHeaders(self, regex_name, regex, owtf_transaction):
        return (self.Grep(regex_name, regex, owtf_transaction.GetResponseHeaders()))

    def Grep(self, regex_name, regex, data):
        results = regex.findall(data)
        output = {}
        if results:
            output.update({regex_name: results})
        return (output)

    @target_required
    def SearchByRegexName(self, regex_name, stats=False, target_id=None):
        """
        Allows searching of the grep_outputs table using a regex name
        What this function returns :
        + regex_name
        + grep_outputs - list of unique matches
        + transaction_ids - list of one transaction id per unique match
        + match_percent
        """
        # Get the grep outputs and only unique values
        grep_outputs = self.db.session.query(
            models.GrepOutput.output).filter_by(
                name=regex_name,
                target_id=target_id).group_by(models.GrepOutput.output).all()
        grep_outputs = [i[0] for i in grep_outputs]
        # Get one transaction per match
        transaction_ids = []
        for grep_output in grep_outputs:
            transaction_ids.append(self.db.session.query(models.Transaction.id).join(
                models.Transaction.grep_outputs).filter(
                    models.GrepOutput.output == grep_output,
                    models.GrepOutput.target_id == target_id).limit(1).all()[0][0])
        # Calculate stats if needed
        if stats:
            # Calculate the total number of matches
            num_matched_transactions = self.db.session.query(models.Transaction).join(
                models.Transaction.grep_outputs).filter(
                    models.GrepOutput.name == regex_name,
                    models.GrepOutput.target_id == target_id).group_by(
                        models.Transaction).count()
            # Calculate total number of transactions in scope
            num_transactions_in_scope = self.db.session.query(models.Transaction).filter_by(
                scope=True,
                target_id=target_id).count()
            # Calculate matched percentage
            if int(num_transactions_in_scope):
                match_percent = int(
                    (num_matched_transactions / float(num_transactions_in_scope)) * 100)
            else:
                match_percent = 0
        else:
            match_percent = None
        return ([
            regex_name,
            [json.loads(i) for i in grep_outputs],
            transaction_ids,
            match_percent])

    @target_required
    def SearchByRegexNames(self, name_list, stats=False, target_id=None):
        """
        Allows searching of the grep_outputs table using a regex name
        What this function returns is a list of list containing
        + regex_name
        + grep_outputs - list of unique matches
        + transaction_ids - list of one transaction id per unique match
        + match_percent
        """
        results = [
            self.SearchByRegexName(regex_name, stats=stats, target_id=target_id)
            for regex_name in name_list]
        return (results)

# ----------------------------- API Methods -----------------------------
    def DeriveTransactionDict(self, tdb_obj, include_raw_data=False):
        # Create a new copy so no accidental changes
        tdict = dict(tdb_obj.__dict__)
        tdict.pop("_sa_instance_state")
        tdict["local_timestamp"] = tdict["local_timestamp"].strftime("%d-%m %H:%M:%S")
        if not include_raw_data:
            tdict.pop("raw_request", None)
            tdict.pop("response_headers", None)
            tdict.pop("response_body", None)
        else:
            if tdict["binary_response"]:
                tdict["response_body"] = base64.b64encode(str(tdict["response_body"]))
        return tdict

    def DeriveTransactionDicts(self, tdb_obj_list, include_raw_data=False):
        return [
            self.DeriveTransactionDict(tdb_obj, include_raw_data)
            for tdb_obj in tdb_obj_list]

    @target_required
    def SearchAll(self, Criteria, target_id=None, include_raw_data=True):
        # Three things needed
        # + Total number of transactions
        # + Filtered transaaction dicts
        # + Filtered number of transactions
        total = self.db.session.query(
            models.Transaction).filter_by(target_id=target_id).count()
        filtered_transaction_objs = self.GenerateQueryUsingSession(
            Criteria,
            target_id).all()
        filtered_number = self.GenerateQueryUsingSession(
            Criteria,
            target_id,
            for_stats=True).count()
        return ({
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self.DeriveTransactionDicts(
                filtered_transaction_objs,
                include_raw_data)})

    @target_required
    def GetAllAsDicts(self, Criteria, target_id=None, include_raw_data=False):
        # Assemble ALL transactions that match the criteria from DB.
        query = self.GenerateQueryUsingSession(Criteria, target_id)
        transaction_objs = query.all()
        return(self.DeriveTransactionDicts(transaction_objs, include_raw_data))

    @target_required
    def GetByIDAsDict(self, trans_id, target_id=None):
        transaction_obj = self.db.session.query(
            models.Transaction).filter_by(
                target_id=target_id,
                id=trans_id).first()
        if not transaction_obj:
            raise InvalidTransactionReference(
                "No transaction with " + str(trans_id) + " exists")
        return self.DeriveTransactionDict(transaction_obj, include_raw_data=True)

    @target_required
    def GetSessionData(self, target_id=None):
        """
        * This will return the data from the `session_tokens` column in the form of a list,
          having no `null` values
        * A sample data: [{"attributes": {"Path": "/", "HttpOnly": true}, "name": "ASP.NET_SessionId", "value": "jx0ydsvwqtfgqcufazwigiih"},
                          {"attributes": {"Path": "/"}, "name": "amSessionId", "value": "618174515"}]
        """
        session_data = self.db.session.query(
            models.Transaction.session_tokens).filter_by(
                target_id=target_id).all()
        results = [json.loads(el[0]) for el in session_data if el and el[0]]
        return (results)

    @target_required
    def GetSessionURLs(self, target_id=None):
        """
        This returns the data in the form of [(url1), (url2), etc]
        """
        session_urls = self.db.session.query(models.Transaction.url).filter(
            models.Transaction.target_id == target_id,
            group_by(models.Transaction.session_tokens)).getall()
        return session_urls
