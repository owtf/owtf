"""
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
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


def run(Core, PluginInfo):
    # Core.Config.Show()
    Content = DESCRIPTION + " Results:<br />"
    for Args in Core.PluginParams.GetArgs({
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

        ret = Core.PluginParams.SetConfig(
            Args)  # Only now, after modifying ATTACHMENT_NAME, update config
    wafbps = wafbypasser.WAFBypasser(Core)
    wafbps.start(format_args(Args))
    return Content