"""
owtf.web.handlers.health
~~~~~~~~~~~~~~~

"""
import json

from owtf.web.handlers.base import UIRequestHandler

__all__ = ['HealthCheckHandler']


class HealthCheckHandler(UIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.write(json.dumps({'ok': True}))
