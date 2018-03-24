"""
owtf.api.health
~~~~~~~~~~~~~~~
"""
from owtf.api.handlers.base import APIRequestHandler

__all__ = ['HealthCheckHandler']


class HealthCheckHandler(APIRequestHandler):
    SUPPORTED_METHODS = ['GET']

    def get(self):
        self.write({'ok': True})
