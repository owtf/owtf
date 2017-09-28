"""
owtf.interface.urls
~~~~~~~~~~~~~~~~~~~

"""

import tornado.web

from owtf.api.handlers.config import ConfigurationHandler
from owtf.api.handlers.misc import ErrorDataHandler, DashboardPanelHandler, ProgressBarHandler
from owtf.api.handlers.plugin import PluginDataHandler, PluginNameOutput
from owtf.api.handlers.report import ReportExportHandler
from owtf.api.handlers.session import OWTFSessionHandler
from owtf.api.handlers.targets import TargetSeverityChartHandler, TargetConfigSearchHandler, TargetConfigHandler
from owtf.api.handlers.transactions import URLDataHandler, URLSearchHandler, TransactionDataHandler, \
    TransactionHrtHandler, TransactionSearchHandler
from owtf.api.handlers.work import WorkerHandler, WorklistHandler, WorklistSearchHandler
from owtf.dependency_management.dependency_resolver import ServiceLocator
from owtf.api.base import StaticFileHandler, FileRedirectHandler


def get_handlers():

    db_plugin = ServiceLocator.get_component("db_plugin")
    config = ServiceLocator.get_component("config")
    plugin_group_re = '(%s)?' % '|'.join(db_plugin.get_all_plugin_groups())
    plugin_type_re = '(%s)?' % '|'.join(db_plugin.get_all_plugin_types())
    plugin_code_re = '([0-9A-Z\-]+)?'

    URLS = [
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

        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': config.get_val('STATICFILES_DIR')}),
        tornado.web.url(r'/output_files/(.*)', FileRedirectHandler, name='file_redirect_url')]
    return URLS


def get_file_server_handlers():
    config = ServiceLocator.get_component("config")
    URLS = [
        tornado.web.url(r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', WorkerHandler, name='workers_api_url'),
        tornado.web.url(r'/api/plugins/progress/?$', ProgressBarHandler, name='poutput_count'),
        tornado.web.url(r'/logs/(.*)', StaticFileHandler, {'path': config.get_dir_worker_logs()}, name="logs_files_url"),
        tornado.web.url(r'/(.*)', StaticFileHandler, {'path': config.get_output_dir_target()}, name="output_files_url"),
    ]
    return URLS
