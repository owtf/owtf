from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.http.wafbypasser import wafbypasser


def format_args(args):
    formatted_args = {"target": None,
                      "payloads": None,
                      "headers": None,
                      "methods": None,
                      "data": None,
                      "contains": None,
                      "resp_code_det": None,
                      "reverse": None,
                      "fuzzing_signature": None,
                      "accepted_value": None,
                      "param_name": None,
                      "param_source": None,
                      "delay": None,
                      "follow_cookies": None,
                      "cookie": None,
                      "length": None,
                      "response_time": None,
                      "mode": None}
    for param, value in dict(args).iteritems():
        formatted_args[param.lower()] = value
    return formatted_args


DESCRIPTION = "WAF byppaser module plugin"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = DESCRIPTION + " Results:<br />"
    plugin_params = ServiceLocator.get_component("plugin_params")
    for Args in plugin_params.GetArgs({
                                              'Description': DESCRIPTION,
                                              'Mandatory': {
                                              'TARGET': None,
                                              'MODE': None,
                                              },
                                              'Optional': {
                                              'METHODS': None,
                                              'COOKIE': None,
                                              'HEADERS': None,
                                              'LENGTH': None,
                                              'DATA': None,
                                              'CONTAINS': None,
                                              'RESP_CODE_DET': None,
                                              'RESPONSE_TIME': None,
                                              'REVERSE': None,
                                              'PAYLOADS': None,
                                              'ACCEPTED_VALUE': None,
                                              'PARAM_NAME': None,
                                              'PARAM_SOURCE': None,
                                              'DELAY': None,
                                              'FOLLOW-COOKIES': None,

                                              }}, PluginInfo):

        ret = plugin_params.SetConfig(
            Args)  # Only now, after modifying ATTACHMENT_NAME, update config
    wafbps = wafbypasser.WAFBypasser(Core)
    wafbps.start(format_args(Args))
    return Content
