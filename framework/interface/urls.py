from framework.interface import api_handlers, ui_handlers
import tornado.web

def get_handlers(Core):

    plugin_group_re = '(' + '|'.join(Core.DB.Plugin.GetAllGroups()) + ')?'
    plugin_type_re = '(' + '|'.join(Core.DB.Plugin.GetAllTypes()) + ')?'
    plugin_code_re = '([0-9A-Z\-]+)?'

    URLS =  [
                tornado.web.url(r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', api_handlers.PluginDataHandler, name='plugins_api_url'),
                tornado.web.url(r'/api/targets/?([0-9]+)?/?$', api_handlers.TargetConfigHandler, name='targets_api_url'),
                tornado.web.url(r'/api/targets/([0-9]+)/urls/?$', api_handlers.URLDataHandler, name='urls_api_url'),
                tornado.web.url(r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', api_handlers.TransactionDataHandler, name='transactions_api_url'),
                tornado.web.url(r'/api/targets/([0-9]+)/poutput/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', api_handlers.PluginOutputHandler, name='poutput_api_url'),
                tornado.web.url(r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', api_handlers.WorkerHandler, name='workers_api_url'),
                tornado.web.url(r'/api/worklist/?$', api_handlers.WorkListHandler, name='worklist_api_url'),
                tornado.web.url(r'/api/configuration/?$', api_handlers.ConfigurationHandler, name='configuration_api_url'),

                (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': Core.Config.FrameworkConfigGet('STATICFILES_DIR')}),
                (r'/output_files/(.*)', tornado.web.StaticFileHandler, {'path': Core.Config.GetOutputDirForTargets()}),
                tornado.web.url(r'/?$', ui_handlers.Redirect, name='redirect_ui_url'),
                tornado.web.url(r'/ui/?$', ui_handlers.Home, name='home_ui_url'),
                tornado.web.url(r'/ui/targets/?([0-9]+)?/?$', ui_handlers.TargetManager, name='targets_ui_url'),
                tornado.web.url(r'/ui/targets/([0-9]+)/transactions/?([0-9]+)?/?$', ui_handlers.TransactionLog, name='transaction_log_url'),
                tornado.web.url(r'/ui/targets/([0-9]+)/urls/?$', ui_handlers.UrlLog, name='url_log_url'),
                tornado.web.url(r'/ui/targets/([0-9]+)/poutput/?', ui_handlers.PluginOutput, name='poutput_ui_url'),
                tornado.web.url(r'/ui/workers/?([0-9])?/?', ui_handlers.WorkerManager, name='workers_ui_url'),
                tornado.web.url(r'/ui/configuration/?$', ui_handlers.ConfigurationManager, name='configuration_ui_url'),
                tornado.web.url(r'/ui/help/?', ui_handlers.Help, name='help_ui_url'),
            ]
    return(URLS)
