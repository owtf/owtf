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
DESCRIPTION = "Spear Phishing Testing plugin"


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
                                                                          'PHISHING_PAYLOAD': config.Get(
                                                                                  'PHISHING_PAYLOAD_DESCRIP'),
                                                                          'SET_FILE_EXTENSION_ATTACK': config.Get(
                                                                                  'SET_FILE_EXTENSION_ATTACK_DESCRIP'),
                                                                          'SET_EMAIL_TEMPLATE': config.Get(
                                                                                  'SET_EMAIL_TEMPLATE_DESCRIP'),
                                                                          'SMTP_LOGIN': config.Get('SMTP_LOGIN_DESCRIP'),
                                                                          'SMTP_PASS': config.Get('SMTP_PASS_DESCRIP'),
                                                                          'SMTP_HOST': config.Get('SMTP_HOST_DESCRIP'),
                                                                          'SMTP_PORT': config.Get('SMTP_PORT_DESCRIP'),
                                                                          'EMAIL_PRIORITY': config.Get(
                                                                                  'EMAIL_PRIORITY_DESCRIP'),
                                                                          'PDF_TEMPLATE': config.Get('PDF_TEMPLATE_DESCRIP'),
                                                                          'WORD_TEMPLATE': config.Get(
                                                                                  'WORD_TEMPLATE_DESCRIP'),
                                                                          'MSF_LISTENER_IP': config.Get(
                                                                                  'MSF_LISTENER_IP_DESCRIP'),
                                                                          'MSF_LISTENER_PORT': config.Get(
                                                                                  'MSF_LISTENER_PORT_DESCRIP'),
                                                                          'MSF_LISTENER_SETUP': config.Get(
                                                                                  'MSF_LISTENER_SETUP_DESCRIP'),
                                                                          'ATTACHMENT_NAME': config.Get(
                                                                                  'ATTACHMENT_NAME_DESCRIP'),
                                                                          'PHISHING_SCRIPT_DIR': config.Get(
                                                                                  'PHISHING_SCRIPT_DIR_DESCRIP')
                                                                          },
                                                                          'Optional': {
                                                                          'PHISHING_CUSTOM_EXE_PAYLOAD_DIR': config.Get(
                                                                                  'PHISHING_CUSTOM_EXE_PAYLOAD_DIR_DESCRIP'),
                                                                          'PHISHING_CUSTOM_EXE_PAYLOAD': config.Get(
                                                                                  'PHISHING_CUSTOM_EXE_PAYLOAD_DESCRIP'),
                                                                          'ISHELL_EXIT_METHOD': config.Get(
                                                                                  'ISHELL_EXIT_METHOD_DESCRIP'),
                                                                          'ISHELL_DELAY_BETWEEN_COMMANDS': config.Get(
                                                                                  'ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
                                                                          'ISHELL_COMMANDS_BEFORE_EXIT': config.Get(
                                                                                  'ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
                                                                          'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.Get(
                                                                                  'ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
                                                                          'REPEAT_DELIM': config.Get('REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        #Let user specify the attachment name:
        #Args['ATTACHMENT_NAME'] = Args['ATTACHMENT_NAME']+"_"+Args['PHISHING_PAYLOAD']+"-"+Args['SET_EMAIL_TEMPLATE']
        plugin_params.SetConfig(
            Args)  # Only now, after modifying ATTACHMENT_NAME, update config
        #print "Args="+str(Args)
        Content += ServiceLocator.get_component("spear_phishing").Run(Args, PluginInfo)
    #Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output', ServiceLocator.get_component("config").GetResources('SendPhishingAttackviaSET'), PluginInfo, Content)
    return Content