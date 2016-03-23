from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.interface import api_handlers, ui_handlers, custom_handlers
import tornado.web


def get_handlers():

    db_plugin = ServiceLocator.get_component("db_plugin")
    config = ServiceLocator.get_component("config")
    plugin_group_re = '(' + '|'.join(db_plugin.GetAllGroups()) + ')?'
    plugin_type_re = '(' + '|'.join(db_plugin.GetAllTypes()) + ')?'
    plugin_code_re = '([0-9A-Z\-]+)?'

    URLS = [
        tornado.web.url(r'/api/errors/?([0-9]+)?/?$', api_handlers.ErrorDataHandler, name='errors_api_url'),
        tornado.web.url(r'/api/sessions/?([0-9]+)?/?(activate|add|remove)?/?$', api_handlers.OWTFSessionHandler, name='owtf_sessions_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/([0-9]+)/forward?$', api_handlers.ForwardToZAPHandler, name='forward_zap_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/([0-9]+)/replay?$', api_handlers.ReplayRequestHandler, name='transaction_replay_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/zest/?$', api_handlers.ZestScriptHandler, name='zest_log_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/zconsole/?$', api_handlers.ZestScriptHandler, name='zest_console_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/([0-9]+)/zest/?$', api_handlers.ZestScriptHandler, name='zest_api_url'),
        tornado.web.url(r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', api_handlers.PluginDataHandler, name='plugins_api_url'),
        tornado.web.url(r'/api/plugins/progress/?$', api_handlers.ProgressBarHandler, name='poutput_count'),
        tornado.web.url(r'/api/targets/search/?$', api_handlers.TargetConfigSearchHandler, name='targets_search_api_url'),
        tornado.web.url(r'/api/targets/?([0-9]+)?/?$', api_handlers.TargetConfigHandler, name='targets_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/urls/?$', api_handlers.URLDataHandler, name='urls_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/urls/search/?$', api_handlers.URLSearchHandler, name='urls_search_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/sessions/?$', api_handlers.SessionsDataHandler, name='sessions_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', api_handlers.TransactionDataHandler, name='transactions_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/transactions/search/?$', api_handlers.TransactionSearchHandler, name='transactions_search_api_url'),
        tornado.web.url(r'/api/targets/([0-9]+)/poutput/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', api_handlers.PluginOutputHandler, name='poutput_api_url'),
        # The following one url is dummy and actually processed in file server
        tornado.web.url(r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', api_handlers.WorkerHandler, name='workers_api_url'),
        tornado.web.url(r'/api/worklist/?([0-9]+)?/?(pause|resume|delete)?/?$', api_handlers.WorklistHandler, name='worklist_api_url'),
        tornado.web.url(r'/api/worklist/search/?$', api_handlers.WorklistSearchHandler, name='worklist_search_api_url'),
        tornado.web.url(r'/api/configuration/?$', api_handlers.ConfigurationHandler, name='configuration_api_url'),
        tornado.web.url(r'/api/plugnhack/?$', api_handlers.PlugnhackHandler, name='plugnhack_api_url'),
        tornado.web.url(r'/api/update/?$', api_handlers.AutoUpdaterHandler, name='auto_updater_api_url'),

        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': config.FrameworkConfigGet('STATICFILES_DIR')}),
        tornado.web.url(r'/output_files/(.*)', ui_handlers.FileRedirectHandler, name='file_redirect_url'),
        tornado.web.url(r'/?$', ui_handlers.Redirect, name='redirect_ui_url'),
        tornado.web.url(r'/ui/?$', ui_handlers.Home, name='home_ui_url'),
        tornado.web.url(r'/ui/targets/?([0-9]+)?/?$', ui_handlers.TargetManager, name='targets_ui_url'),
        tornado.web.url(r'/ui/targets/([0-9]+)/transactions/zconsole?$', ui_handlers.ZestScriptConsoleHandler, name='zest_console_url'),
        tornado.web.url(r'/ui/targets/([0-9]+)/transactions/([0-9]+)/replay?$', ui_handlers.ReplayRequest, name='transaction_replay_url'),
        tornado.web.url(r'/ui/targets/([0-9]+)/transactions/?([0-9]+)?/?$', ui_handlers.TransactionLog, name='transaction_log_url'),
        tornado.web.url(r'/ui/targets/([0-9]+)/sessions/?$', ui_handlers.HTTPSessions, name='sessions_ui_url'),
        tornado.web.url(r'/ui/targets/([0-9]+)/urls/?$', ui_handlers.UrlLog, name='url_log_url'),
        tornado.web.url(r'/ui/targets/([0-9]+)/poutput/?', ui_handlers.PluginOutput, name='poutput_ui_url'),
        tornado.web.url(r'/ui/workers/?([0-9])?/?', ui_handlers.WorkerManager, name='workers_ui_url'),
        tornado.web.url(r'/ui/worklist/?', ui_handlers.WorklistManager, name='worklist_ui_url'),
        tornado.web.url(r'/ui/configuration/?$', ui_handlers.ConfigurationManager, name='configuration_ui_url'),
        tornado.web.url(r'/ui/plugnhack/?', ui_handlers.PlugnHack, name='plugnhack_ui_url'),
        tornado.web.url(r'/ui/plugnhack/?(.*)', ui_handlers.PlugnHack, name='plugnhack_ui_manifest_url'),
        tornado.web.url(r'/ui/help/?', ui_handlers.Help, name='help_ui_url')]
    return (URLS)


def get_file_server_handlers():
    config = ServiceLocator.get_component("config")
    URLS = [
        tornado.web.url(r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', api_handlers.WorkerHandler, name='workers_api_url'),
        tornado.web.url(r'/(.*)', custom_handlers.StaticFileHandler, {'path': config.GetOutputDirForTargets()}, name="output_files_url"),
    ]
    return(URLS)
