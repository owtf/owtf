"""
owtf.api.handlers.transactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import logging

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.lib.exceptions import InvalidParameterType, InvalidTargetReference, InvalidTransactionReference, APIError
from owtf.managers.transaction import (
    delete_transaction,
    get_all_transactions_dicts,
    get_by_id_as_dict,
    get_hrt_response,
    search_all_transactions,
)
from owtf.managers.url import get_all_urls, search_all_urls
from owtf.api.handlers.jwtauth import jwtauth

__all__ = [
    "TransactionDataHandler",
    "TransactionHrtHandler",
    "TransactionSearchHandler",
    "URLDataHandler",
    "URLSearchHandler",
]


@jwtauth
class TransactionDataHandler(APIRequestHandler):
    """Handle transaction data for the target by ID or all."""

    SUPPORTED_METHODS = ["GET", "DELETE"]

    def get(self, target_id=None, transaction_id=None):
        """Get transaction data by target and transaction id.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/5/transactions/2/ HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Encoding: gzip
            Vary: Accept-Encoding
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "binary_response": false,
                    "response_headers": "Content-Length: 9605\\r\\nExpires: -1\\r\\nX-Aspnet-Version: 2.0.50727",
                    "target_id": 5,
                    "session_tokens": "{}",
                    "logout": null,
                    "raw_request": "GET http://demo.testfire.net/ HTTP/1.1",
                    "time_human": "0s, 255ms",
                    "data": "",
                    "id": 2,
                    "url": "http://demo.testfire.net/",
                    "response_body": "",
                    "local_timestamp": "01-04 15:42:08",
                    "response_size": 9605,
                    "response_status": "200 OK",
                    "scope": true,
                    "login": null,
                    "method": "GET"
                }
            }
        """
        try:
            if transaction_id:
                self.success(get_by_id_as_dict(self.session, int(transaction_id), target_id=int(target_id)))
            else:
                # Empty criteria ensure all transactions
                filter_data = dict(self.request.arguments)
                self.success(get_all_transactions_dicts(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidTransactionReference:
            raise APIError(400, "Invalid transaction referenced")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")

    def post(self, target_url):
        raise APIError(405)

    def put(self):
        raise APIError(405)

    def patch(self):
        raise APIError(405)

    def delete(self, target_id=None, transaction_id=None):
        """Delete a transaction.

        **Example request**:

        .. sourcecode:: http

            DELETE /api/v1/targets/5/transactions/2/ HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "status": "success",
                "data": null
            }
        """
        try:
            if transaction_id:
                delete_transaction(self.session, int(transaction_id), int(target_id))
                self.success(None)
            else:
                raise APIError(400, "Needs transaction id")
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")


@jwtauth
class TransactionHrtHandler(APIRequestHandler):
    """Integrate HTTP request translator tool."""

    SUPPORTED_METHODS = ["POST"]

    def post(self, target_id=None, transaction_id=None):
        """Get the transaction as output from the tool.

        **Example request**:

        .. sourcecode:: http

            POST /api/v1/targets/5/transactions/hrt/2/ HTTP/1.1
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest
            Content-Length: 13


            language=bash

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Length: 594
            Content-Type: text/html; charset=UTF-8


            #!/usr/bin/env bash
            curl -v --request GET http://demo.testfire.net/  --header "Accept-Language: en-US,en;q=0.5"  \
            --header "Accept-Encoding: gzip, deflate"
        """
        try:
            if transaction_id:
                filter_data = dict(self.request.arguments)
                self.write(get_hrt_response(self.session, filter_data, int(transaction_id), target_id=int(target_id)))
            else:
                raise APIError(400, "Needs transaction id")
        except InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except InvalidTransactionReference:
            raise APIError(400, "Invalid transaction referenced")
        except InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")


@jwtauth
class TransactionSearchHandler(APIRequestHandler):
    """Search transaction data in the DB."""

    SUPPORTED_METHODS = ["GET"]

    def get(self, target_id=None):
        """Get transactions by target ID.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/targets/5/transactions/search/ HTTP/1.1
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json; charset=UTF-8

            {
                "status": "success",
                "data": {
                    "records_total": 0,
                    "records_filtered": 0,
                    "data": []
                }
            }
        """
        if not target_id:  # Must be a integer target id
            raise APIError(400, "Missing target_id")
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            filter_data["search"] = True
            self.success(search_all_transactions(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference:
            raise APIError(400, "Invalid target reference provided")
        except exceptions.InvalidTransactionReference:
            raise APIError(400, "Invalid transaction referenced")
        except exceptions.InvalidParameterType:
            raise APIError(400, "Invalid parameter type provided")


# To be deprecated!
class URLDataHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["GET"]

    def get(self, target_id=None):
        try:
            # Empty criteria ensure all transactions
            filter_data = dict(self.request.arguments)
            self.write(get_all_urls(self.session, filter_data, target_id=int(target_id)))
        except exceptions.InvalidTargetReference as e:
            logging.warn(e.parameter)
            raise tornado.web.HTTPError(400)

    @tornado.gen.coroutine
    def post(self, target_url):
        raise tornado.web.HTTPError(405)

    @tornado.gen.coroutine
    def put(self):
        raise tornado.web.HTTPError(405)

    @tornado.gen.coroutine
    def patch(self):
        # TODO: allow modification of urls from the ui, may be adjusting scope etc.. but i don't understand
        # it's use yet ;)
        raise tornado.web.HTTPError(405)  # @UndefinedVariable

    @tornado.gen.coroutine
    def delete(self, target_id=None):
        # TODO: allow deleting of urls from the ui
        raise tornado.web.HTTPError(405)  # @UndefinedVariable


class URLSearchHandler(APIRequestHandler):
    SUPPORTED_METHODS = ["GET"]

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
