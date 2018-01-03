"""
owtf.api.handlers.config
~~~~~~~~~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.web
import tornado.httpclient

from owtf.lib import exceptions
from owtf.api.base import APIRequestHandler


class ConfigurationHandler(APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH')

    def get(self):
        filter_data = dict(self.request.arguments)
        self.write(get_config_dicts(filter_data))

    def patch(self):
        for key, value_list in list(self.request.arguments.items()):
            try:
                update(key, value_list[0])
            except exceptions.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)

