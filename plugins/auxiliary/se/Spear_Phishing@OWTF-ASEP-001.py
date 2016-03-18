from framework.dependency_management.dependency_resolver import ServiceLocator

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
