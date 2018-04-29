"""
owtf.files.routes
~~~~~~~~~~~~~~~~~

"""
import tornado.web

from owtf.files.handlers import StaticFileHandler
from owtf.utils.file import get_dir_worker_logs, get_output_dir_target

HANDLERS = [
    tornado.web.url(r"/logs/(.*)", StaticFileHandler, {"path": get_dir_worker_logs()}, name="logs_files_url"),
    tornado.web.url(r"/(.*)", StaticFileHandler, {"path": get_output_dir_target()}, name="output_files_url"),
]
