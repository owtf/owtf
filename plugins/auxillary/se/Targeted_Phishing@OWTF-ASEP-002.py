from framework.dependency_management.dependency_resolver import ServiceLocator

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
