"""
owtf.api.handlers.index
~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.api.handlers.base import UIRequestHandler


class IndexHandler(UIRequestHandler):

    def get(self, path):
        self.render('index.html')
