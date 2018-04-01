"""
owtf.api.handlers.config
~~~~~~~~~~~~~~~~~~~~~~~~

"""
import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.managers.config import get_all_config_dicts, update_config_val

__all__ = ['ConfigurationHandler']


class ConfigurationHandler(APIRequestHandler):
    """Update framework settings and tool paths."""

    SUPPORTED_METHODS = ['GET', 'PATCH']

    def get(self):
        """Return all configuration items.

        **Example request**:

        .. sourcecode:: http

            GET /api/v1/configuration HTTP/1.1
            Accept: application/json

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept-Encoding


            [
               {
                  "dirty":false,
                  "section":"AUX_PLUGIN_DATA",
                  "value":"report",
                  "descrip":"Filename for the attachment to be sent",
                  "key":"ATTACHMENT_NAME"
               },
               {
                  "dirty":false,
                  "section":"DICTIONARIES",
                  "value":"hydra",
                  "descrip":"",
                  "key":"BRUTEFORCER"
               }
            ]
        """
        filter_data = dict(self.request.arguments)
        self.write(get_all_config_dicts(self.session, filter_data))

    def patch(self):
        """Update configuration item

        **Example request**:

        .. sourcecode:: http

            PATCH /api/v1/configuration/ HTTP/1.1
            Accept: */*
            Content-Type: application/x-www-form-urlencoded; charset=UTF-8
            X-Requested-With: XMLHttpRequest

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept-Encoding
            Content-Length: 0
            Content-Type: text/html; charset=UTF-8
        """
        for key, value_list in list(self.request.arguments.items()):
            try:
                update_config_val(self.session, key, value_list[0])
            except exceptions.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)
