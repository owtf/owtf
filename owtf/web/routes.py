"""
owtf.web.routes
~~~~~~~~~~~~~~~

Routes for the web interface.
"""
import tornado.web

from owtf.settings import STATIC_ROOT
from owtf.web.handlers.redirect import FileRedirectHandler
from owtf.web.handlers.health import HealthCheckHandler
from owtf.web.handlers.index import IndexHandler

UI_HANDLERS = [
    tornado.web.url(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': STATIC_ROOT}),
    tornado.web.url(r'/debug/health/?$', HealthCheckHandler),
    tornado.web.url(r'/output_files/(.*)', FileRedirectHandler, name='file_redirect_url'),
    tornado.web.url(r'^/(?!api|debug|static|output_files)(.*)$', IndexHandler)
]
