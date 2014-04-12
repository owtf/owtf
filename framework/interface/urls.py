from framework.interface import api_handlers

def get_handlers(Core):

    plugin_group_re = '(' + '|'.join(Core.DB.Plugin.GetAllGroups()) + ')?'
    plugin_type_re = '(' + '|'.join(Core.DB.Plugin.GetAllTypes()) + ')?'
    plugin_code_re = '([0-9A-Z\-]+)?'

    URLS =  [
                (r'/api/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', api_handlers.PluginDataHandler),
                (r'/api/targets/?([0-9]+)?/?$', api_handlers.TargetConfigHandler),
                (r'/api/targets/([0-9]+)/urls/?$', api_handlers.URLDataHandler),
                (r'/api/targets/([0-9]+)/transactions/?([0-9]+)?/?$', api_handlers.TransactionDataHandler),
                (r'/api/targets/([0-9]+)/plugins/?' + plugin_group_re + '/?' + plugin_type_re + '/?' + plugin_code_re + '/?$', api_handlers.PluginOutputHandler),
                (r'/api/workers/?([0-9]+)?/?(abort|pause|resume)?/?$', api_handlers.WorkerHandler),
                (r'/api/worklist/?$', api_handlers.WorkListHandler),
            ]
    return(URLS)
