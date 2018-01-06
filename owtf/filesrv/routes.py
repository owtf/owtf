import tornado.web

from owtf.filesrv.handlers import StaticFileHandler
from owtf.api.handlers.misc import ProgressBarHandler
from owtf.api.handlers.work import WorkerHandler
from owtf.utils.file import get_output_dir_target, get_dir_worker_logs


HANDLERS = [

    tornado.web.url(r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', WorkerHandler, name='workers_api_url'),
    tornado.web.url(r'/api/plugins/progress/?$', ProgressBarHandler, name='poutput_count'),
    tornado.web.url(r'/logs/(.*)', StaticFileHandler, {'path': get_dir_worker_logs()}, name="logs_files_url"),
    tornado.web.url(r'/(.*)', StaticFileHandler, {'path': get_output_dir_target()}, name="output_files_url"),

]
