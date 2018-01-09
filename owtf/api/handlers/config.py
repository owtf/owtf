"""
owtf.api.handlers.config
~~~~~~~~~~~~~~~~~~~~~

"""

import tornado.gen
import tornado.httpclient
import tornado.web

from owtf.api.handlers.base import APIRequestHandler
from owtf.lib import exceptions
from owtf.managers.config import get_all_config_dicts, update_config_val


class ConfigurationHandler(APIRequestHandler):
    SUPPORTED_METHODS = ('GET', 'PATCH')

    def get(self):
        filter_data = dict(self.request.arguments)
        self.write(get_all_config_dicts(self.session, filter_data))

    def patch(self):
        for key, value_list in list(self.request.arguments.items()):
            try:
                update_config_val(self.session, key, value_list[0])
            except exceptions.InvalidConfigurationReference:
                raise tornado.web.HTTPError(400)

