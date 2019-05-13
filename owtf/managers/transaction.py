"""
owtf.managers.transaction
~~~~~~~~~~~~~~~~~~~~~~~~~
The DB stores HTTP transactions, unique URLs and more.
"""
import base64
from collections import defaultdict
import json
import logging
import re

from hrt.interface import HttpRequestTranslator
from sqlalchemy import asc, desc

from owtf.config import config_handler
from owtf.db.session import get_count, get_scoped_session
from owtf.transactions.base import HTTPTransaction
from owtf.lib.exceptions import InvalidParameterType, InvalidTransactionReference
from owtf.managers.target import target_required
from owtf.managers.url import import_processed_url
from owtf.models.grep_output import GrepOutput
from owtf.models.transaction import Transaction
from owtf.utils.strings import get_header_list, str2bool

# The regex find differs for these types :P
REGEX_TYPES = ["HEADERS", "BODY"]


@target_required
def num_transactions(session, scope=True, target_id=None):
    """Return number of transactions in scope by default

    :param scope: In/out scope
    :type scope: `bool`
    :param target_id: ID of the target
    :type target_id: `int`
    :return: Number of transactions in scope
    :rtype: `int`
    """
    count = get_count(
        session.query(Transaction).filter_by(scope=scope, target_id=target_id)
    )
    return count


@target_required
def is_transaction_already_added(session, criteria, target_id=None):
    """Checks if the transaction is already in the DB

    :param criteria: Filter criteria
    :type criteria: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :return: True/False
    :rtype: `bool`
    """
    return len(get_all_transactions(session, criteria, target_id=target_id)) > 0


def transaction_gen_query(session, criteria, target_id, for_stats=False):
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
    query = session.query(Transaction).filter_by(target_id=target_id)
    # If transaction search is being done
    if criteria.get("search", None):
        if criteria.get("url", None):
            if isinstance(criteria.get("url"), list):
                criteria["url"] = criteria["url"][0]
            query = query.filter(
                Transaction.url.like("%%{!s}%%".format(criteria["url"]))
            )
        if criteria.get("method", None):
            if isinstance(criteria.get("method"), list):
                criteria["method"] = criteria["method"][0]
            query = query.filter(
                Transaction.method.like("%%{!s}%%".format(criteria.get("method")))
            )
        if criteria.get("data", None):
            if isinstance(criteria.get("data"), list):
                criteria["data"] = criteria["data"][0]
            query = query.filter(
                Transaction.data.like("%%{!s}%%".format(criteria.get("data")))
            )
        if criteria.get("raw_request", None):
            if isinstance(criteria.get("raw_request"), list):
                criteria["raw_request"] = criteria["raw_request"][0]
            query = query.filter(
                Transaction.raw_request.like(
                    "%%{!s}%%".format(criteria.get("raw_request"))
                )
            )
        if criteria.get("response_status", None):
            if isinstance(criteria.get("response_status"), list):
                criteria["response_status"] = criteria["response_status"][0]
            query = query.filter(
                Transaction.response_status.like(
                    "%%{!s}%%".format(criteria.get("response_status"))
                )
            )
        if criteria.get("response_headers", None):
            if isinstance(criteria.get("response_headers"), list):
                criteria["response_headers"] = criteria["response_headers"][0]
            query = query.filter(
                Transaction.response_headers.like(
                    "%%{!s}%%".format(criteria.get("response_headers"))
                )
            )
        if criteria.get("response_body", None):
            if isinstance(criteria.get("response_body"), list):
                criteria["response_body"] = criteria["response_body"][0]
            query = query.filter(
                Transaction.binary_response is False,
                Transaction.response_body.like(
                    "%%{!s}%%".format(criteria.get("response_body"))
                ),
            )
    else:  # If transaction filter is being done
        if criteria.get("url", None):
            if isinstance(criteria.get("url"), str):
                query = query.filter_by(url=criteria["url"])
            if isinstance(criteria.get("url"), list):
                query = query.filter(Transaction.url.in_(criteria.get("url")))
        if criteria.get("method", None):
            if isinstance(criteria.get("method"), str):
                query = query.filter_by(method=criteria["method"])
            if isinstance(criteria.get("method"), list):
                query = query.filter(Transaction.method.in_(criteria.get("method")))
        if criteria.get("data", None):
            if isinstance(criteria.get("data"), str):
                query = query.filter_by(data=criteria["data"])
            if isinstance(criteria.get("data"), list):
                query = query.filter(Transaction.data.in_(criteria.get("data")))
    # For the following section doesn't matter if filter/search because
    # it doesn't make sense to search in a boolean column :P
    if criteria.get("scope", None):
        if isinstance(criteria.get("scope"), list):
            criteria["scope"] = criteria["scope"][0]
        query = query.filter_by(scope=str2bool(criteria["scope"]))
    if criteria.get("binary_response", None):
        if isinstance(criteria.get("binary_response"), list):
            criteria["binary_response"] = criteria["binary_response"][0]
        query = query.filter_by(binary_response=str2bool(criteria["binary_response"]))
    if not for_stats:  # query for stats shouldn't have limit and offset
        try:
            query.order_by(Transaction.local_timestamp)
            if criteria.get("offset", None):
                if isinstance(criteria.get("offset"), list):
                    criteria["offset"] = int(criteria["offset"][0])
                if criteria["offset"] >= 0:
                    query = query.offset(criteria["offset"])
            if criteria.get("limit", None):
                if isinstance(criteria.get("limit"), list):
                    criteria["limit"] = int(criteria["limit"][0])
                if criteria["limit"] >= 0:
                    query = query.limit(criteria["limit"])
            else:  # It is too dangerous without a limit argument
                query.limit(10)  # Default limit value is 10
        except ValueError:
            raise InvalidParameterType("Invalid parameter type for transaction db")
    return query


@target_required
def get_first(session, criteria, target_id=None):
    """Assemble only the first transaction that matches the criteria from DB

    :param criteria: Filter criteria
    :type criteria: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :return:
    :rtype:
    """
    query = transaction_gen_query(session, criteria, target_id)
    return get_transaction(query.first())


@target_required
def get_all_transactions(session, criteria, target_id=None):
    """Assemble ALL transactions that match the criteria from DB

    :param criteria: Filter criteria
    :type criteria: `dict`
    :param target_id: target ID
    :type target_id: `int`
    :return:
    :rtype:
    """
    query = transaction_gen_query(session, criteria, target_id)
    return get_transactions(query.all())


def get_transaction(trans):
    """Fetch transaction from the DB

    :param trans: OWTF transaction
    :type trans: :`Class:transaction.HTTP_Transaction`
    :return:
    :rtype:
    """
    if trans:
        owtf_transaction = HTTPTransaction(None)
        response_body = trans.response_body
        if trans.binary_response:
            response_body = base64.b64decode(response_body)
        owtf_transaction.set_transaction_from_db(
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
            response_body,
        )
        return owtf_transaction
    return None


def get_transactions(transactions):
    """Get multiple transactions from the DB

    :param transactions: List of transactions objects
    :type transactions: `list`
    :return: List of transactions
    :rtype: `list`
    """
    return [
        get_transaction(transaction)
        for transaction in transactions
        if transaction is not None
    ]


def get_transaction_model(transaction):
    """Generate object to be added to the DB

    :param transaction: OWTF transaction
    :type transaction: `Class:transaction.HTTP_Transaction`
    :return: Transaction object
    :rtype: `Class:model.Transaction`
    """
    response_body = None
    binary_response = None
    try:
        response_body = transaction.get_raw_response_body.encode("utf-8")
        binary_response = False
    except UnicodeDecodeError:
        response_body = base64.b64encode(transaction.get_raw_response_body)
        binary_response = True
    finally:
        transaction_model = Transaction(
            url=transaction.url,
            scope=transaction.in_scope,
            method=transaction.method,
            data=transaction.data,
            time=float(transaction.time),
            time_human=transaction.time_human,
            local_timestamp=transaction.local_timestamp,
            raw_request=transaction.get_raw_request,
            response_status=transaction.get_status,
            response_headers=transaction.get_response_headers,
            response_body=response_body,
            response_size=len(response_body) if response_body is not None else 0,
            binary_response=binary_response,
            session_tokens=json.dumps(transaction.get_session_tokens()),
        )
        return transaction_model


@target_required
def log_transactions(session, transaction_list, target_id=None):
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
        transaction_model = get_transaction_model(transaction_obj)
        transaction_model.target_id = target_id
        transaction_model_list.append(transaction_model)
        session.add(transaction_model)
        urls_list.append([transaction_obj.url, True, transaction_obj.in_scope])
    session.commit()
    # Now since we have the ids ready, we can process the grep output and
    # add accordingly. So iterate over transactions and their
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
            grep_outputs = grep_transaction(owtf_transaction)
            if grep_outputs:  # If valid grep results exist
                # Iterate over regex_name and regex results
                for regex_name, regex_results in grep_outputs.items():
                    # Then iterate over the results to store each result in
                    # a separate row, but also check to avoid duplicate
                    # entries as we have many-to-many relationship
                    # available for linking
                    for match in regex_results:
                        # Convert the match to json
                        match = json.dumps(match)
                        # Fetch if any existing entry
                        existing_grep_output = session.query(GrepOutput).filter_by(
                            target_id=target_id, name=regex_name, output=match
                        ).first()
                        if existing_grep_output:
                            existing_grep_output.transactions.append(transaction_model)
                            session.merge(existing_grep_output)
                        else:
                            session.add(
                                GrepOutput(
                                    target_id=target_id,
                                    transactions=[transaction_model],
                                    name=regex_name,
                                    output=match,
                                )
                            )
    session.commit()
    import_processed_url(session=session, urls_list=urls_list, target_id=target_id)


def log_transactions_from_logger(transactions_dict):
    """Logs transactions as they come into the DB

    .. note::
        Transaction_dict is a dictionary with target_id as key and list of owtf transactions

    :param transactions_dict: Dict of target id and corresponding owtf transactions
    :type transactions_dict: `dict`
    :return: None
    :rtype: None
    """
    session = get_scoped_session()
    for target_id, transaction_list in list(transactions_dict.items()):
        if transaction_list:
            log_transactions(
                session=session, transaction_list=transaction_list, target_id=target_id
            )


@target_required
def delete_transaction(session, transaction_id, target_id=None):
    """Deletes transaction from DB

    :param transaction_id: transaction ID
    :type transaction_id: `int`
    :param target_id: target ID
    :type target_id: `int`
    :return: None
    :rtype: None
    """
    session.query(Transaction).filter_by(
        target_id=target_id, id=transaction_id
    ).delete()
    session.commit()


@target_required
def get_num_transactions_inscope(target_id=None):
    """Gets number of transactions in scope

    :param target_id: target ID
    :type target_id: `int`
    :return: Number of transactions in scopes
    :rtype: `int`
    """
    return num_transactions(target_id=target_id)


def get_transaction_by_id(id):
    """Get transaction object by id

    :param id: ID to fetch
    :type id: `int`
    :return: Transaction object
    :rtype: `Class:model.Transaction`
    """
    session = get_scoped_session()

    model_obj = None
    try:
        id = int(id)
        model_obj = session.query(Transaction).get(id)
    except ValueError:
        pass
    finally:
        return model_obj  # None returned if no such transaction.


def get_transactions_by_id(id_list):
    """Get transactions by id list

    :param id_list: List of ids
    :type id_list: `list`
    :return: List of transaction objects
    :rtype: `list`
    """
    model_objs = []
    for id in id_list:
        model_obj = get_transaction_by_id(id)
        if model_obj:
            model_objs.append(model_obj)
    return get_transactions(model_objs)


@target_required
def get_top_by_speed(session, order="Desc", num=10, target_id=None):
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
        results = session.query(Transaction).filter_by(target_id=target_id).order_by(
            desc(Transaction.time)
        ).limit(
            num
        )
    else:
        results = session.query(Transaction).filter_by(target_id=target_id).order_by(
            asc(Transaction.time)
        ).limit(
            num
        )
    return get_transactions(results)


def compile_header_regex(header_list):
    """Compile a regex

    :param header_list: List of header strings
    :type header_list: `list`
    :return:
    :rtype:
    """
    return re.compile("(%s): ([^\r]*)" % "|".join(header_list), re.IGNORECASE)


def compile_response_regex(regexp):
    """Compile a response regex

    :param regexp: Regex
    :type regexp: `str`
    :return:
    :rtype:
    """
    return re.compile(regexp, re.IGNORECASE | re.DOTALL)


def compile_regex():
    """General function for getting and compiling regexes

    :return: None
    :rtype: None
    """
    for key in list(config_handler.get_framework_config_dict.keys()):
        key = key[3:-3]  # Remove "@@@"
        if key.startswith("HEADERS"):
            header_list = get_header_list(key)
            regexes["HEADERS"][key] = compile_header_regex(header_list)
        elif key.startswith("RESPONSE"):
            _, _, python_regexp = config_handler.get_val(key).split("_____")
            regexes["BODY"][key] = compile_response_regex(python_regexp)


def grep_transaction(owtf_transaction):
    """Grep transaction

    :param owtf_transaction: OWTF transaction
    :type owtf_transaction:
    :return: Output
    :rtype: `dict`
    """
    grep_output = {}
    for regex_name, regex in list(regexes["HEADERS"].items()):
        grep_output.update(grep_response_headers(regex_name, regex, owtf_transaction))
    for regex_name, regex in list(regexes["BODY"].items()):
        grep_output.update(grep_response_body(regex_name, regex, owtf_transaction))
    return grep_output


def grep_response_body(regex_name, regex, owtf_transaction):
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
    return grep(regex_name, regex, owtf_transaction.get_raw_response_body)


def grep_response_headers(regex_name, regex, owtf_transaction):
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
    return grep(regex_name, regex, owtf_transaction.get_response_headers)


def grep(regex_name, regex, data):
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
def search_by_regex_name(session, regex_name, stats=False, target_id=None):
    """Allows searching of the grep_outputs table using a regex name

    .. note::
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
    grep_outputs = session.query(GrepOutput.output).filter_by(
        name=regex_name, target_id=target_id
    ).group_by(
        GrepOutput.output
    ).all()
    grep_outputs = [i[0] for i in grep_outputs]
    # Get one transaction per match
    transaction_ids = []
    for grep_output in grep_outputs:
        transaction_ids.append(
            session.query(Transaction.id).join(Transaction.grep_outputs).filter(
                GrepOutput.output == grep_output, GrepOutput.target_id == target_id
            ).limit(
                1
            ).all()[
                0
            ][
                0
            ]
        )
    # Calculate stats if needed
    if stats:
        # Calculate the total number of matches
        num_matched_transactions = get_count(
            session.query(Transaction).join(Transaction.grep_outputs).filter(
                GrepOutput.name == regex_name, GrepOutput.target_id == target_id
            ).group_by(
                Transaction
            )
        )
        # Calculate total number of transactions in scope
        num_transactions_in_scope = get_count(
            session.query(Transaction).filter_by(scope=True, target_id=target_id)
        )
        # Calculate matched percentage
        if int(num_transactions_in_scope):
            match_percent = int(
                (num_matched_transactions / float(num_transactions_in_scope)) * 100
            )
        else:
            match_percent = 0
    else:
        match_percent = None
    return [
        regex_name,
        [json.loads(i) for i in grep_outputs],
        transaction_ids,
        match_percent,
    ]


@target_required
def search_by_regex_names(name_list, stats=False, target_id=None):
    """Allows searching of the grep_outputs table using a regex name

    .. note::
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
    session = get_scoped_session()
    results = [
        search_by_regex_name(session, regex_name, stats=stats, target_id=target_id)
        for regex_name in name_list
    ]
    return results


def get_transaction_dicts(tdb_obj_list, include_raw_data=False):
    """Derive a list of transaction dicts from an object list

    :param tdb_obj_list: List of transaction objects
    :type tdb_obj_list: `list`
    :param include_raw_data: true/false to include raw transactions
    :type include_raw_data: `bool`
    :return: List of transaction dicts
    :rtype: `list`
    """
    return [tdb_obj.to_dict(include_raw_data) for tdb_obj in tdb_obj_list]


@target_required
def search_all_transactions(session, criteria, target_id=None, include_raw_data=True):
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
    total = get_count(session.query(Transaction).filter_by(target_id=target_id))
    filtered_transaction_objs = transaction_gen_query(
        session, criteria, target_id
    ).all()
    filtered_number = get_count(
        transaction_gen_query(session, criteria, target_id, for_stats=True)
    )
    results = {
        "records_total": total,
        "records_filtered": filtered_number,
        "data": get_transaction_dicts(filtered_transaction_objs, include_raw_data),
    }
    return results


@target_required
def get_all_transactions_dicts(
    session, criteria, target_id=None, include_raw_data=False
):
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
    query = get_all_transactions(session, criteria, target_id)
    transaction_objs = query.all()
    return get_transaction_dicts(transaction_objs, include_raw_data)


@target_required
def get_by_id_as_dict(session, trans_id, target_id=None):
    """Get transaction dict by ID

    :param trans_id: Transaction ID
    :type trans_id: `int`
    :param target_id: Target ID
    :type target_id: `int`
    :return: transaction object as dict
    :rtype: `dict`
    """
    transaction_obj = session.query(Transaction).filter_by(
        target_id=target_id, id=trans_id
    ).first()
    if not transaction_obj:
        raise InvalidTransactionReference(
            "No transaction with {!s} exists".format(trans_id)
        )
    return transaction_obj.to_dict(include_raw_data=True)


@target_required
def get_hrt_response(session, filter_data, trans_id, target_id=None):
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
    transaction_obj = session.query(Transaction).filter_by(
        target_id=target_id, id=trans_id
    ).first()

    # Data validation
    languages = ["bash"]  # Default script language is set to bash.
    if filter_data.get("language"):
        languages = [x.strip() for x in filter_data["language"]]

    proxy = None
    search_string = None
    data = None
    if filter_data.get("proxy"):
        proxy = filter_data["proxy"][0]
    if filter_data.get("search_string"):
        search_string = filter_data["search_string"][0]
    if filter_data.get("data"):
        data = filter_data["data"][0]
    # If target not found. Raise error.
    if not transaction_obj:
        raise InvalidTransactionReference(
            "No transaction with {!s} exists".format(trans_id)
        )
    raw_request = transaction_obj.raw_request
    try:
        hrt_obj = HttpRequestTranslator(
            request=raw_request,
            languages=languages,
            proxy=proxy,
            search_string=search_string,
            data=data,
        )
        codes = hrt_obj.generate_code()
        return "".join(v for v in list(codes.values()))
    except Exception as e:
        logging.error("Unexpected exception when running HRT: $s", str(e))
        return str(e)


regexes = defaultdict(list)
for regex_type in REGEX_TYPES:
    regexes[regex_type] = {}
compile_regex()
