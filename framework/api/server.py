from framework.lib.general import cprint
from framework.lib import general
from framework.api import work_handlers, plugindb_handlers, targetdb_handlers
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
                                                                (r'/api/targets/?([0-9]+)?/?$', targetdb_handlers.TargetConfigHandler),
                                                                (r'/api/targets/([0-9]+)/urls/?$', targetdb_handlers.URLDataHandler),
                                                                (r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', targetdb_handlers.TransactionDataHandler),
                                                                (r'/api/targets/([0-9]+)/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', targetdb_handlers.PluginOutputHandler),
                                                                (r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', plugindb_handlers.PluginDataHandler),
                                                                (r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', work_handlers.WorkerHandler),
                                                                (r'/api/worklist/?$', work_handlers.WorkListHandler),
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
