import tornado.web

from owtf.db.database import Session, get_db_engine


class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        Session.configure(bind=get_db_engine())
        self.session = Session()
        self.sentry_client = kwargs.pop("sentry_client", None)
        super(Application, self).__init__(*args, **kwargs)
