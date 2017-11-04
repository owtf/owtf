"""
owtf.db.transaction_manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DB stores HTTP transactions, unique URLs and more.
"""

import re
import json
import base64
import logging
from collections import defaultdict

from sqlalchemy import desc, asc
from hrt.interface import HttpRequestTranslator

from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import TransactionInterface
from owtf.managers.target import target_required
from owtf.lib.exceptions import InvalidTransactionReference, InvalidParameterType
from owtf.http import transaction
from owtf.db import models


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
        self.regexs = defaultdict(list)
        for regex_type in REGEX_TYPES:
            self.regexs[regex_type] = {}
        self.compile_regex()

    @target_required
    def num_transactions(self, scope=True, target_id=None):
        """Return number of transactions in scope by default

        :param scope: In/out scope
        :type scope: `bool`
        :param target_id: ID of the target
        :type target_id: `int`
        :return: Number of transactions in scope
        :rtype: `int`
        """
        count = self.db.session.query(models.Transaction).filter_by(scope=scope, target_id=target_id).count()
        return count

    @target_required
    def is_already_added(self, criteria, target_id=None):
        """Checks if the transaction is already in the DB

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: Target ID
        :type target_id: `int`
        :return: True/False
        :rtype: `bool`
        """
        return len(self.get_all(criteria, target_id=target_id)) > 0

    def gen_query(self, criteria, target_id, for_stats=False):
        """Generate query based on criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: Target ID
        :type target_id: `int`
        :param for_stats: True/False
        :type for_stats: `bool`
        :return: 
        :rtype:
        """
        query = self.db.session.query(models.Transaction).filter_by(target_id=target_id)
        # If transaction search is being done
        if criteria.get('search', None):
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), list):
                    criteria['url'] = criteria['url'][0]
                query = query.filter(models.Transaction.url.like('%%%s%%' % criteria['url']))
            if criteria.get('method', None):
                if isinstance(criteria.get('method'), list):
                    criteria['method'] = criteria['method'][0]
                query = query.filter(models.Transaction.method.like('%%%s%%' % criteria.get('method')))
            if criteria.get('data', None):
                if isinstance(criteria.get('data'), list):
                    criteria['data'] = criteria['data'][0]
                query = query.filter(models.Transaction.data.like('%%%s%%' % criteria.get('data')))
            if criteria.get('raw_request', None):
                if isinstance(criteria.get('raw_request'), list):
                    criteria['raw_request'] = criteria['raw_request'][0]
                query = query.filter(models.Transaction.raw_request.like('%%%s%%' % criteria.get('raw_request')))
            if criteria.get('response_status', None):
                if isinstance(criteria.get('response_status'), list):
                    criteria['response_status'] = criteria['response_status'][0]
                query = query.filter(models.Transaction.response_status.like('%%%s%%' %
                                                                             criteria.get('response_status')))
            if criteria.get('response_headers', None):
                if isinstance(criteria.get('response_headers'), list):
                    criteria['response_headers'] = criteria['response_headers'][0]
                query = query.filter(models.Transaction.response_headers.like('%%%s%%' %
                                                                              criteria.get('response_headers')))
            if criteria.get('response_body', None):
                if isinstance(criteria.get('response_body'), list):
                    criteria['response_body'] = criteria['response_body'][0]
                query = query.filter(models.Transaction.binary_response is False,
                                     models.Transaction.response_body.like('%%%s%%' % criteria.get('response_body')))
        else:  # If transaction filter is being done
            if criteria.get('url', None):
                if isinstance(criteria.get('url'), str):
                    query = query.filter_by(url=criteria['url'])
                if isinstance(criteria.get('url'), list):
                    query = query.filter(models.Transaction.url.in_(criteria.get('url')))
            if criteria.get('method', None):
                if isinstance(criteria.get('method'), str):
                    query = query.filter_by(method=criteria['method'])
                if isinstance(criteria.get('method'), list):
                    query = query.filter(models.Transaction.method.in_(criteria.get('method')))
            if criteria.get('data', None):
                if isinstance(criteria.get('data'), str):
                    query = query.filter_by(data=criteria['data'])
                if isinstance(criteria.get('data'), list):
                    query = query.filter(models.Transaction.data.in_(criteria.get('data')))
        # For the following section doesn't matter if filter/search because
        # it doesn't make sense to search in a boolean column :P
        if criteria.get('scope', None):
            if isinstance(criteria.get('scope'), list):
                criteria['scope'] = criteria['scope'][0]
            query = query.filter_by(scope=self.config.str2bool(criteria['scope']))
        if criteria.get('binary_response', None):
            if isinstance(criteria.get('binary_response'), list):
                criteria['binary_response'] = criteria['binary_response'][0]
            query = query.filter_by(binary_response=self.config.str2bool(criteria['binary_response']))
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
                raise InvalidParameterType("Invalid parameter type for transaction db")
        return query

    @target_required
    def get_first(self, criteria, target_id=None):
        """Assemble only the first transaction that matches the criteria from DB

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: Target ID
        :type target_id: `int`
        :return:
        :rtype:
        """
        query = self.gen_query(criteria, target_id)
        return self.get_transaction(query.first())

    @target_required
    def get_all(self, criteria, target_id=None):
        """Assemble ALL transactions that match the criteria from DB

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: target ID
        :type target_id: `int`
        :return:
        :rtype:
        """
        query = self.gen_query(criteria, target_id)
        return self.get_transactions(query.all())

    def get_transaction(self, trans):
        """Fetch transaction from the DB

        :param trans: OWTF transaction
        :type trans: :`Class:transaction.HTTP_Transaction`
        :return:
        :rtype:
        """
        if trans and len(trans) > 0:
            owtf_transaction = transaction.HTTP_Transaction(None)
            response_body = trans.response_body
            if trans.binary_response:
                response_body = base64.b64decode(response_body)
            owtf_transaction.set_transaction_from_db(trans.id, trans.url, trans.method, trans.response_status,
                                                     str(trans.time), trans.time_human, trans.local_timestamp, trans.data,
                                                     trans.raw_request, trans.response_headers, len(response_body),
                                                     response_body)
            return owtf_transaction
        return None

    def get_transactions(self, transactions):
        """Get multiple transactions from the DB

        :param transactions: List of transactions objects
        :type transactions: `list`
        :return: List of transactions
        :rtype: `list`
        """
        return [self.get_transaction(transaction) for transaction in transactions if
                self.get_transaction(transaction) is not None]

    def get_transaction_model(self, transaction):
        """Generate object to be added to the DB

        :param transaction: OWTF transaction
        :type transaction::`Class:transaction.HTTP_Transaction`
        :return: Transaction object
        :rtype::`Class:model.Transaction`
        """
        try:
            response_body = transaction.get_raw_response_body().encode("utf-8")
            binary_response = False
        except UnicodeDecodeError:
            response_body = base64.b64encode(transaction.get_raw_response_body())
            binary_response = True
        finally:
            transaction_model = models.Transaction(
                url=transaction.url,
                scope=transaction.in_scope(),
                method=transaction.method,
                data=transaction.data,
                time=float(transaction.time),
                time_human=transaction.time_human,
                local_timestamp=transaction.local_timestamp,
                raw_request=transaction.get_raw_request(),
                response_status=transaction.get_status(),
                response_headers=transaction.get_response_headers(),
                response_body=response_body,
                response_size=len(response_body),
                binary_response=binary_response,
                session_tokens=transaction.get_session_tokens(),
                login=None,
                logout=None
            )
            return transaction_model

    @target_required
    def log_transactions(self, transaction_list, target_id=None):
        """This function does the following things in order
            + Add all transactions to a session and commit
            + Add all the grepped results and commit
            + Add all urls to url db

        :param transaction_list: List of transaction objects
        :type transaction_list: `list`
        :param target_id: target ID
        :type target_id: `int`
        :return:
        :rtype:
        """
        # Create a usable session
        # Initiate urls_list for holding urls and transaction_model_list for holding transaction models
        urls_list = []
        transaction_model_list = []
        # Add transactions and commit so that we can have access to
        # transaction ids etc..
        for transaction_obj in transaction_list:
            # TODO: This shit will go crazy on non-ascii characters
            transaction_model = self.get_transaction_model(transaction_obj)
            transaction_model.target_id = target_id
            transaction_model_list.append(transaction_model)
            self.db.session.add(transaction_model)
            urls_list.append([transaction_obj.url, True, transaction_obj.in_scope()])
        self.db.session.commit()
        # Now since we have the ids ready, we can process the grep output and
        # add accordingly. So iterate over transactions and their models.
        for i, obj in enumerate(transaction_list):
            # Get the transaction and transaction model from their lists
            owtf_transaction = transaction_list[i]
            transaction_model = transaction_model_list[i]
            # Check if grepping is valid for this transaction
            # For grepping to be valid
            # + Transaction must not have a binary response
            # + Transaction must be in scope
            if (not transaction_model.binary_response) and (transaction_model.scope):
                # Get the grep results
                grep_outputs = self.grep_transaction(owtf_transaction)
                if grep_outputs:  # If valid grep results exist
                    # Iterate over regex_name and regex results
                    for regex_name, regex_results in grep_outputs.items():
                        # Then iterate over the results to store each result in
                        # a seperate row, but also check to avoid duplicate
                        # entries as we have many-to-many relationship
                        # available for linking
                        for match in regex_results:
                            # Conver the match to json
                            match = json.dumps(match)
                            # Fetch if any existing entry
                            existing_grep_output = self.db.session.query(models.GrepOutput).filter_by(
                                target_id=target_id, name=regex_name, output=match).first()
                            if existing_grep_output:
                                existing_grep_output.transactions.append(transaction_model)
                                self.db.session.merge(existing_grep_output)
                            else:
                                self.db.session.add(models.GrepOutput(target_id=target_id,
                                                                      transactions=[transaction_model],
                                                                      name=regex_name,
                                                                      output=match))
        self.db.session.commit()
        self.url_manager.import_processed_url(urls_list, target_id=target_id)

    def log_transactions_from_logger(self, transactions_dict):
        """Logs transactions as they come into the DB

        .note::
            Transaction_dict is a dictionary with target_id as key and list of owtf transactions

        :param transactions_dict: Dict of target id and corresponding owtf transactions
        :type transactions_dict: `dict`
        :return: None
        :rtype: None
        """
        for target_id, transaction_list in list(transactions_dict.items()):
            if transaction_list:
                self.log_transactions(transaction_list, target_id=target_id)

    @target_required
    def delete_transaction(self, transaction_id, target_id=None):
        """Deletes transaction from DB

        :param transaction_id: transaction ID
        :type transaction_id: `int`
        :param target_id: target ID
        :type target_id: `int`
        :return: None
        :rtype: None
        """
        self.db.session.query(models.Transaction).filter_by(target_id=target_id, id=transaction_id).delete()
        self.db.session.commit()

    @target_required
    def get_num_transactions_inscope(self, target_id=None):
        """Gets number of transactions in scope

        :param target_id: target ID
        :type target_id: `int`
        :return: Number of transactions in scopes
        :rtype: `int`
        """
        return self.num_transactions(target_id=target_id)

    def get_by_id(self, id):
        """Get transaction object by id

        :param id: ID to fetch
        :type id: `int`
        :return: Transaction object
        :rtype::`Class:model.Transaction`
        """
        model_obj = None
        try:
            id = int(id)
            model_obj = self.db.session.query(models.Transaction).get(id)
        except ValueError:
            pass
        finally:
            return model_obj  # None returned if no such transaction.

    def get_by_ids(self, id_list):
        """Get transactions by id list

        :param id_list: List of ids
        :type id_list: `list`
        :return: List of transaction objects
        :rtype: `list`
        """
        model_objs = []
        for id in id_list:
            model_obj = self.get_by_id(id)
            if model_obj:
                model_objs.append(model_obj)
        return self.get_transactions(model_objs)

    @target_required
    def get_top_by_speed(self, order="Desc", num=10, target_id=None):
        """Get top transactions by speed

        :param order: Ascending/descending order
        :type order: `str`
        :param num: Num of transactions to fetch
        :type num: `int`
        :param target_id: target ID
        :type target_id: `int`
        :return: List of transactions
        :rtype: `list`
        """
        if order == "Desc":
            results = self.db.session.query(models.Transaction).filter_by(target_id=target_id).order_by(
                desc(models.Transaction.time)).limit(num)
        else:
            results = self.db.session.query(models.Transaction).filter_by(target_id=target_id).order_by(
                asc(models.Transaction.time)).limit(num)
        return self.get_transactions(results)

    def compile_header_regex(self, header_list):
        """Compile a regex

        :param header_list: List of header strings
        :type header_list: `list`
        :return:
        :rtype:
        """
        return re.compile('(%s): ([^\r]*)' % '|'.join(header_list), re.IGNORECASE)

    def compile_response_regex(self, regexp):
        """Compile a response regex

        :param regexp: Regex
        :type regexp: `str`
        :return:
        :rtype:
        """
        return re.compile(regexp, re.IGNORECASE | re.DOTALL)

    def compile_regex(self):
        """General function for getting and compiling regexes

        :return: None
        :rtype: None
        """
        for key in list(self.config.get_framework_config_dict().keys()):
            key = key[3:-3]  # Remove "@@@"
            if key.startswith('HEADERS'):
                header_list = self.config.get_header_list(key)
                self.regexs['HEADERS'][key] = self.compile_header_regex(header_list)
            elif key.startswith('RESPONSE'):
                _, _, python_regexp = self.config.get_val(key).split('_____')
                self.regexs['BODY'][key] = self.compile_response_regex(python_regexp)

    def grep_transaction(self, owtf_transaction):
        """Grep transaction

        :param owtf_transaction: OWTF transaction
        :type owtf_transaction:
        :return: Output
        :rtype: `dict`
        """
        grep_output = {}
        for regex_name, regex in list(self.regexs['HEADERS'].items()):
            grep_output.update(self.grep_response_headers(regex_name, regex, owtf_transaction))
        for regex_name, regex in list(self.regexs['BODY'].items()):
            grep_output.update(self.grep_response_body(regex_name, regex, owtf_transaction))
        return grep_output

    def grep_response_body(self, regex_name, regex, owtf_transaction):
        """Grep response body

        :param regex_name: Regex name
        :type regex_name: `str`
        :param regex: Regex
        :type regex:
        :param owtf_transaction: OWTF transaction
        :type owtf_transaction:
        :return: Output
        :rtype: `dict`
        """
        return self.grep(regex_name, regex, owtf_transaction.get_raw_response_body())

    def grep_response_headers(self, regex_name, regex, owtf_transaction):
        """Grep response headers

        :param regex_name: Name of regex
        :type regex_name: `str`
        :param regex: Regex
        :type regex:
        :param owtf_transaction: OWTF transaction
        :type owtf_transaction:
        :return: Output
        :rtype: `dict`
        """
        return self.grep(regex_name, regex, owtf_transaction.get_response_headers())

    def grep(self, regex_name, regex, data):
        """Run regex

        :param regex_name: Name of regex
        :type regex_name: `str`
        :param regex: Regex
        :type regex:
        :param data: Data
        :type data: `str`
        :return: Output from grep
        :rtype: `dict`
        """
        results = regex.findall(data)
        output = {}
        if results:
            output.update({regex_name: results})
        return output

    @target_required
    def search_by_regex_name(self, regex_name, stats=False, target_id=None):
        """Allows searching of the grep_outputs table using a regex name

        .note::
            What this function returns :
            + regex_name
            + grep_outputs - list of unique matches
            + transaction_ids - list of one transaction id per unique match
            + match_percent

        :param regex_name: Name of regex
        :type regex_name: `str`
        :param stats: true/false
        :type stats: `bool`
        :param target_id: target ID
        :type target_id: `int`
        :return: List of results
        :rtype: `list`
        """
        # Get the grep outputs and only unique values
        grep_outputs = self.db.session.query(models.GrepOutput.output).filter_by(
            name=regex_name, target_id=target_id).group_by(models.GrepOutput.output).all()
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
                    models.GrepOutput.target_id == target_id).group_by(models.Transaction).count()
            # Calculate total number of transactions in scope
            num_transactions_in_scope = self.db.session.query(models.Transaction).filter_by(
                scope=True, target_id=target_id).count()
            # Calculate matched percentage
            if int(num_transactions_in_scope):
                match_percent = int((num_matched_transactions / float(num_transactions_in_scope)) * 100)
            else:
                match_percent = 0
        else:
            match_percent = None
        return [regex_name, [json.loads(i) for i in grep_outputs], transaction_ids, match_percent]

    @target_required
    def search_by_regex_names(self, name_list, stats=False, target_id=None):
        """Allows searching of the grep_outputs table using a regex name

        .note::
            What this function returns is a list of list containing
            + regex_name
            + grep_outputs - list of unique matches
            + transaction_ids - list of one transaction id per unique match
            + match_percent

        :param name_list: List of names
        :type name_list: `list`
        :param stats: True/false
        :type stats: `bool`
        :param target_id: target ID
        :type target_id: `int`
        :return: List of matched ids
        :rtype: `list`
        """
        results = [self.search_by_regex_name(regex_name, stats=stats, target_id=target_id) for regex_name in name_list]
        return results

    def get_transaction_dict(self, tdb_obj, include_raw_data=False):
        """Derive a transaction dict from an object

        :param tdb_obj_list: Transaction object
        :type tdb_obj_list:
        :param include_raw_data: true/false to include raw transactions
        :type include_raw_data: `bool`
        :return: transaction dict
        :rtype: `dict`
        """
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

    def get_transaction_dicts(self, tdb_obj_list, include_raw_data=False):
        """Derive a list of transaction dicts from an object list

        :param tdb_obj_list: List of transaction objects
        :type tdb_obj_list: `list`
        :param include_raw_data: true/false to include raw transactions
        :type include_raw_data: `bool`
        :return: List of transaction dicts
        :rtype: `list`
        """
        return [self.get_transaction_dict(tdb_obj, include_raw_data) for tdb_obj in tdb_obj_list]

    @target_required
    def search_all(self, criteria, target_id=None, include_raw_data=True):
        """Search all transactions.Three things needed
            + Total number of transactions
            + Filtered transaction dicts
            + Filtered number of transactions

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: target ID
        :type target_id: `int`
        :param include_raw_data: True/False to include raw data
        :type include_raw_data: `bool`
        :return: Results
        :rtype: `dict`
        """
        total = self.db.session.query(models.Transaction).filter_by(target_id=target_id).count()
        filtered_transaction_objs = self.gen_query(criteria, target_id).all()
        filtered_number = self.gen_query(criteria, target_id, for_stats=True).count()
        results = {
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self.get_transaction_dicts(filtered_transaction_objs, include_raw_data)
        }
        return results

    @target_required
    def get_all_as_dicts(self, criteria, target_id=None, include_raw_data=False):
        """Assemble ALL transactions that match the criteria from DB.

        :param criteria: Filter criteria
        :type criteria: `dict`
        :param target_id: target ID
        :type target_id: `int`
        :param include_raw_data: True/False as to include raw data
        :type include_raw_data: `bool`
        :return: List of transaction dicts
        :rtype: `list`
        """
        query = self.gen_query(criteria, target_id)
        transaction_objs = query.all()
        return self.get_transaction_dicts(transaction_objs, include_raw_data)

    @target_required
    def get_by_id_as_dict(self, trans_id, target_id=None):
        """Get transaction dict by ID

        :param trans_id: Transaction ID
        :type trans_id: `int`
        :param target_id: Target ID
        :type target_id: `int`
        :return: transaction object as dict
        :rtype: `dict`
        """
        transaction_obj = self.db.session.query(models.Transaction).filter_by(target_id=target_id, id=trans_id).first()
        if not transaction_obj:
            raise InvalidTransactionReference("No transaction with %s exists" % str(trans_id))
        return self.get_transaction_dict(transaction_obj, include_raw_data=True)

    @target_required
    def get_hrt_response(self, filter_data, trans_id, target_id=None):
        """Converts the transaction and calls hrt

        :param filter_data: Filter data
        :type filter_data: `dict`
        :param trans_id: Transaction ID
        :type trans_id: `int`
        :param target_id: Target ID
        :type target_id: `int`
        :return: Converted code
        :rtype: `string`
        """
        transaction_obj = self.db.session.query(models.Transaction).filter_by(target_id=target_id, id=trans_id).first()

        # Data validation
        languages = ['bash']  # Default script language is set to bash.
        if filter_data.get('language'):
            languages = [x.strip() for x in filter_data['language']]

        proxy = None
        search_string = None
        data = None

        if filter_data.get('proxy'):
            proxy = filter_data['proxy'][0]

        if filter_data.get('search_string'):
            search_string = filter_data['search_string'][0]

        if filter_data.get('data'):
            data = filter_data['data'][0]

        # If target not found. Raise error.
        if not transaction_obj:
            raise InvalidTransactionReference("No transaction with %s exists" % str(trans_id))

        raw_request = transaction_obj.raw_request

        try:
            hrt_obj = HttpRequestTranslator(
                request=raw_request,
                languages=languages,
                proxy=proxy,
                search_string=search_string,
                data=data)
            codes = hrt_obj.generate_code()
            return ''.join(v for v in list(codes.values()))
        except Exception as e:
            logging.error('Unexpected exception when running HRT: %s' % e)
            return str(e)

    @target_required
    def get_session_data(self, target_id=None):
        """This will return the data from the `session_tokens` column in the form of a list, having no `null` values

        Some sample data:
        [{
            "attributes": {
                "Path": "/",
                "HttpOnly": true
            },
            "name": "ASP.NET_SessionId",
            "value": "jx0ydsvwqtfgqcufazwigiih"
            }, {
                "attributes": {
                    "Path": "/"
                },
                "name": "amSessionId",
                "value": "618174515"
        }]

        :param target_id: target ID
        :type target_id: `int`
        :return: List of cookie dicts
        :rtype: `list`
        """
        session_data = self.db.session.query(models.Transaction.session_tokens).filter_by(target_id=target_id).all()
        results = [json.loads(el[0]) for el in session_data if el and el[0]]
        return results
