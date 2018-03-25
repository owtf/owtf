"""
owtf.web.handlers.base
~~~~~~~~~~~~~~~~~~~~~~

Base handlers.
"""
from tornado.web import RequestHandler

__all__ = ['UIRequestHandler']


class UIRequestHandler(RequestHandler):

    def reverse_url(self, name, *args):
        url = super(UIRequestHandler, self).reverse_url(name, *args)
        url = url.replace('?', '')
        return url.split('None')[0]
