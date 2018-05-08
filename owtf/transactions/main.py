"""
owtf.transactions.main
~~~~~~~~~~~~~~~~~~~~~~
Inbound Proxy Module developed by Bharadwaj Machiraju (blog.tunnelshade.in) as a part of Google Summer of Code 2013
"""
import glob
import logging
import os
import time

try:  # PY3
    from urllib.parse import urlparse
except ImportError:  # PY2
    from urlparse import urlparse

from owtf.transactions.base import HTTPTransaction
from owtf.lib.owtf_process import OWTFProcess
from owtf.models.target import Target
from owtf.managers.target import get_all_in_scope, target_manager
from owtf.managers.transaction import log_transactions_from_logger
from owtf.proxy.cache_handler import request_from_cache, response_from_cache
from owtf.settings import INBOUND_PROXY_CACHE_DIR
from owtf.utils.timer import Timer


class TransactionLogger(OWTFProcess):
    """
    This transaction logging process is started separately from tornado proxy
    This logger checks for \*.rd files in cache_dir and saves it as owtf db
    transaction, \*.rd files serve as a message that the file corresponding
    to the hash is ready to be converted.
    """

    def initialize(self, **kwargs):
        self.logger.disable_console_logging()

    def derive_target_for_transaction(self, request, response, target_list, host_list):
        """Get the target and target ID for transaction

        :param request: Proxy request
        :type request:
        :param response: Proxy response
        :type response:
        :param target_list: The target list for the transaction
        :type target_list: `list`
        :param host_list: The list of hosts for the transaction
        :type host_list: `list`
        :return:
        :rtype: `list`
        """
        for target_id, target in target_list:
            if request.url.startswith(target):
                return [target_id, True]
            elif target in request.url:
                return [target_id, self.get_scope_for_url(request.url, host_list)]
            elif response.headers.get("Referer", None) and response.headers["Referer"].startswith(target):
                return [target_id, self.get_scope_for_url(request.url, host_list)]
            # This check must be at the last
            elif urlparse(request.url).hostname == urlparse(target).hostname:
                return [target_id, True]
        return [target_manager.get_target_id, self.get_scope_for_url(request.url, host_list)]

    def get_scope_for_url(self, url, host_list):
        """Check the scope for the url in the transaction

        :param url: URL to inspect
        :type url: `str`
        :param host_list: The list of hosts associated
        :type host_list: `list`
        :return: True if in scope, else False
        :rtype: `bool`
        """
        return urlparse(url).hostname in host_list

    def get_owtf_transactions(self, hash_list):
        """Get the proxy transactions from the cache

        :param hash_list: The hash list to fetch from cache
        :type hash_list: `list`
        :return: A dictionary of all requested transactions
        :rtype: `dict`
        """
        transactions_dict = None
        target_list = Target.get_indexed(self.session)
        if target_list:  # If there are no targets in db, where are we going to add. OMG
            transactions_dict = {}
            host_list = get_all_in_scope("host_name")

            for request_hash in hash_list:
                request = request_from_cache(os.path.join(INBOUND_PROXY_CACHE_DIR, request_hash))
                response = response_from_cache(os.path.join(INBOUND_PROXY_CACHE_DIR, request_hash))
                target_id, request.in_scope = self.derive_target_for_transaction(
                    request, response, target_list, host_list
                )
                owtf_transaction = HTTPTransaction(Timer())
                owtf_transaction.import_proxy_req_resp(request, response)
                try:
                    transactions_dict[target_id].append(owtf_transaction)
                except KeyError:
                    transactions_dict[target_id] = [owtf_transaction]
        return transactions_dict

    def get_hash_list(self, cache_dir):
        """Returns the hash list from cache directory

        :param cache_dir: The path to the cache directory
        :type cache_dir: `str`
        :return: List of hashes
        :rtype: `list`
        """
        hash_list = []
        for file_path in glob.glob(os.path.join(cache_dir, "*.rd")):
            request_hash = os.path.basename(file_path)[:-3]
            hash_list.append(request_hash)
            os.remove(file_path)
        return hash_list

    def pseudo_run(self):
        """The run function which fetches the transactions from the cache asynchronously

        :return: None
        :rtype: None
        """
        try:
            while self.poison_q.empty():
                if glob.glob(os.path.join(INBOUND_PROXY_CACHE_DIR, "*.rd")):
                    hash_list = self.get_hash_list(INBOUND_PROXY_CACHE_DIR)
                    transactions_dict = self.get_owtf_transactions(hash_list)
                    if transactions_dict:  # Make sure you do not have None
                        log_transactions_from_logger(transactions_dict)
                else:
                    time.sleep(2)
        except KeyboardInterrupt:
            exit(-1)


def start_transaction_logger():
    try:
        transaction_logger = TransactionLogger(cache_dir=INBOUND_PROXY_CACHE_DIR)
        transaction_logger.initialize()
        logging.debug("Starting transaction logger process")
        transaction_logger.start()
    except Exception as exc:
        logging.debug(str(exc))
        pass
