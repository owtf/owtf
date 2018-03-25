"""
owtf.web.handlers.index
~~~~~~~~~~~~~~~~~~~~~~~

"""
from owtf.web.handlers.base import UIRequestHandler


class IndexHandler(UIRequestHandler):

    def get(self, path):
        self.render('index.html')
