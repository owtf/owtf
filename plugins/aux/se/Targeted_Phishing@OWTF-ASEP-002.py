from framework.dependency_management.dependency_resolver import ServiceLocator

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
DESCRIPTION = "Targeted Phishing Testing plugin"


def run(PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = DESCRIPTION + " Results:<br />"
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    for Args in plugin_params.GetArgs({
                                                                          'Description': DESCRIPTION,
                                                                          'Mandatory': {
                                                                          'EMAIL_TARGET': config.Get('EMAIL_TARGET_DESCRIP'),
                                                                          'EMAIL_FROM': config.Get('EMAIL_FROM_DESCRIP'),
                                                                          'SMTP_LOGIN': config.Get('SMTP_LOGIN_DESCRIP'),
                                                                          'SMTP_PASS': config.Get('SMTP_PASS_DESCRIP'),
                                                                          'SMTP_HOST': config.Get('SMTP_HOST_DESCRIP'),
                                                                          'SMTP_PORT': config.Get('SMTP_PORT_DESCRIP'),
                                                                          'EMAIL_PRIORITY': config.Get(
                                                                                  'EMAIL_PRIORITY_DESCRIP'),
                                                                          'EMAIL_SUBJECT': config.Get(
                                                                                  'EMAIL_SUBJECT_DESCRIP'),
                                                                          'EMAIL_BODY': config.Get('EMAIL_BODY_DESCRIP'),
                                                                          },
                                                                          'Optional': {
                                                                          'EMAIL_ATTACHMENT': config.Get(
                                                                                  'EMAIL_ATTACHMENT_DESCRIP'),
                                                                          'REPEAT_DELIM': config.Get('REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)  # Update config
        #print "Args="+str(Args)
        if ServiceLocator.get_component("smtp").Send(Args):
            Content += "Email delivered succcessfully"
        else:
            Content += "Email delivery failed"
        #Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', ServiceLocator.get_component("config").GetResources('SendPhishingAttackviaSET'), PluginInfo, Content)
    return Content