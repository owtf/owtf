from framework.lib.general import cprint
from framework.lib import general
from framework.api import work_handler, plugin_handler, target_handler
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
import json

class ApiServer(object):
    def __init__(self, Core):
        plugin_group_re = '(' + '|'.join(Core.DB.Plugin.GetAllGroups()) + ')?'
        plugin_type_re = '(' + '|'.join(Core.DB.Plugin.GetAllTypes()) + ')?'
        plugin_code_re = '([0-9A-Z\-]+)?'
        self.application = tornado.web.Application(
                                                    handlers=[
                                                                (r'/api/targets/?([0-9]+)?/?$', target_handler.TargetConfigHandler),
                                                                (r'/api/targets/([0-9]+)/urls/?$', target_handler.URLDataHandler),
                                                                (r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', target_handler.TransactionDataHandler),
                                                                (r'/api/targets/([0-9]+)/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', target_handler.PluginOutputHandler),
                                                                (r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', plugin_handler.PluginDataHandler),
                                                                (r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', work_handler.WorkerHandler),
                                                                (r'/api/worklist/?$', work_handler.WorkListHandler),
                                                            ],
                                                    debug=False,
                                                    gzip=True
                                                  )
        self.application.Core = Core
        self.server = tornado.httpserver.HTTPServer(self.application)
        self.manager_cron = tornado.ioloop.PeriodicCallback(self.application.Core.WorkerManager.manage_workers, 2000)

    def start(self):
        try:
            self.server.bind(8009)
            tornado.options.parse_command_line(args=["dummy_arg","--log_file_prefix=/tmp/ui.log","--logging=info"])
            self.server.start(1)
            self.manager_cron.start()
            tornado.ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
