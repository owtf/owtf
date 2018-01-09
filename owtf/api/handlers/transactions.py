"""
owtf.api.handlers.transactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.lib.exceptions import InvalidTargetReference, InvalidParameterType, InvalidTransactionReference
from owtf.managers.transaction import get_by_id_as_dict, get_all_transactions_dicts, delete_transaction, \
    get_hrt_response, search_all_transactions
from owtf.managers.url import get_all_urls, search_all_urls


class TransactionDataHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET', 'DELETE']

    def get(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                self.write(get_by_id_as_dict(self.session, int(transaction_id), target_id=int(target_id)))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.write(get_all_transactions_dicts(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    def put(self):
        raise tornado.web.HTTPError(405)

    def patch(self):
        raise tornado.web.HTTPError(405)

    def delete(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                delete_transaction(self.session, int(transaction_id), int(target_id))
            else:
                raise tornado.web.HTTPError(400)
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class TransactionHrtHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['POST']

    def post(self, target_id=None, transaction_id=None):
        try:
            if transaction_id:
                filter_data = dict(self.request.arguments)
                self.write(get_hrt_response(self.session, filter_data, int(transaction_id), target_id=int(target_id)))
            else:
                raise tornado.web.HTTPError(400)
        except (InvalidTargetReference, InvalidTransactionReference, InvalidParameterType) as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class TransactionSearchHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:  # Must be a integer target id
            raise tornado.web.HTTPError(400)
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(search_all_transactions(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidTransactionReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)


class URLDataHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            self.write(get_all_urls(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.web.asynchronous
    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.web.asynchronous
    def patch(self):
        # TODO: allow modification of urls from the ui, may be adjusting scope etc.. but i don't understand
        # it's use yet ;)
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.web.asynchronous
    def delete(self, target_id=None):
        # TODO: allow deleting of urls from the ui
        raise tornado.web.HTTPError(405)  # @UndefinedVariable


class URLSearchHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self, target_id=None):
        if not target_id:  # Must be a integer target id
            raise tornado.web.HTTPError(400)
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.write(search_all_urls(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
        except exceptions.InvalidParameterType as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)
