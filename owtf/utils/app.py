"""
owtf.utils.app
~~~~~~~~~~~~~~

"""
import tornado.web

try:
    from raven.contrib.tornado import AsyncSentryClient

    raven_installed = True
except ImportError:
    raven_installed = False

from owtf.settings import USE_SENTRY
from owtf.utils.error import get_sentry_client


class Application(tornado.web.Application):

    def __init__(self, *args, **kwargs):
        if raven_installed and USE_SENTRY:
            self.sentry_client = get_sentry_client()
        super(Application, self).__init__(*args, **kwargs)
