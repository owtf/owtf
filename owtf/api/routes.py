"""
owtf.interface.urls
~~~~~~~~~~~~~~~~~~~

"""

import tornado.web

from owtf.api.handlers import ui_handlers
from owtf.api.handlers.config import ConfigurationHandler
from owtf.api.handlers.misc import ErrorDataHandler, DashboardPanelHandler, ProgressBarHandler
from owtf.api.handlers.plugin import PluginDataHandler, PluginNameOutput, PluginOutputHandler
from owtf.api.handlers.report import ReportExportHandler
from owtf.api.handlers.session import OWTFSessionHandler
from owtf.api.handlers.targets import TargetSeverityChartHandler, TargetConfigSearchHandler, TargetConfigHandler
from owtf.api.handlers.transactions import URLDataHandler, URLSearchHandler, TransactionDataHandler, \
    TransactionHrtHandler, TransactionSearchHandler
from owtf.api.handlers.work import WorkerHandler, WorklistHandler, WorklistSearchHandler
from owtf.db.database import get_scoped_session
from owtf.managers.plugin import get_all_plugin_groups, get_all_plugin_types
from owtf.settings import STATIC_ROOT


session = get_scoped_session()

plugin_group_re = '(%s)?' % '|'.join(get_all_plugin_groups(session))
plugin_type_re = '(%s)?' % '|'.join(get_all_plugin_types(session))
plugin_code_re = '([0-9A-Z\-]+)?'


HANDLERS = [
    tornado.web.url(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': STATIC_ROOT}),
    tornado.web.url(r'/output_files/(.*)', ui_handlers.FileRedirectHandler, name='file_redirect_url'),

    tornado.web.url(r'/api/errors/?([0-9]+)?/?$', ErrorDataHandler, name='errors_api_url'),
    tornado.web.url(r'/api/sessions/?([0-9]+)?/?(activate|add|remove)?/?$', OWTFSessionHandler, name='owtf_sessions_api_url'),
    tornado.web.url(r'/api/dashboard/severitypanel/?$', DashboardPanelHandler),
    tornado.web.url(r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', PluginDataHandler, name='plugins_api_url'),
    tornado.web.url(r'/api/plugins/progress/?$', ProgressBarHandler, name='poutput_count'),
    tornado.web.url(r'/api/targets/severitychart/?$', TargetSeverityChartHandler, name='targets_severity'),
    tornado.web.url(r'/api/targets/search/?$', TargetConfigSearchHandler, name='targets_search_api_url'),
    tornado.web.url(r'/api/targets/?([0-9]+)?/?$', TargetConfigHandler, name='targets_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/urls/?$', URLDataHandler, name='urls_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/urls/search/?$', URLSearchHandler, name='urls_search_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', TransactionDataHandler, name='transactions_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/transactions/search/?$', TransactionSearchHandler, name='transactions_search_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/transactions/hrt/?([0-9]+)?/?$', TransactionHrtHandler, name='transactions_hrt_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/poutput/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', PluginOutputHandler, name='poutput_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/poutput/names/?$', PluginNameOutput, name='plugin_name_api_url'),
    tornado.web.url(r'/api/targets/([0-9]+)/export/?$', ReportExportHandler, name='report_export_api_url'),

    # The following one url is dummy and actually processed in file server
    tornado.web.url(r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', WorkerHandler, name='workers_api_url'),
    tornado.web.url(r'/api/worklist/?([0-9]+)?/?(pause|resume|delete)?/?$', WorklistHandler, name='worklist_api_url'),
    tornado.web.url(r'/api/worklist/search/?$', WorklistSearchHandler, name='worklist_search_api_url'),
    tornado.web.url(r'/api/configuration/?$', ConfigurationHandler, name='configuration_api_url'),
    tornado.web.url(r'^/(?!api|static|output_files)(.*)$', ui_handlers.Index)
]
