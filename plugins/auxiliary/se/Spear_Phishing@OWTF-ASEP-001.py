from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Spear Phishing Testing plugin"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'EMAIL_TARGET': config.FrameworkConfigGet('EMAIL_TARGET_DESCRIP'),
            'EMAIL_FROM': config.FrameworkConfigGet('EMAIL_FROM_DESCRIP'),
            'PHISHING_PAYLOAD': config.FrameworkConfigGet('PHISHING_PAYLOAD_DESCRIP'),
            'SET_FILE_EXTENSION_ATTACK': config.FrameworkConfigGet('SET_FILE_EXTENSION_ATTACK_DESCRIP'),
            'SET_EMAIL_TEMPLATE': config.FrameworkConfigGet('SET_EMAIL_TEMPLATE_DESCRIP'),
            'SMTP_LOGIN': config.FrameworkConfigGet('SMTP_LOGIN_DESCRIP'),
            'SMTP_PASS': config.FrameworkConfigGet('SMTP_PASS_DESCRIP'),
            'SMTP_HOST': config.FrameworkConfigGet('SMTP_HOST_DESCRIP'),
            'SMTP_PORT': config.FrameworkConfigGet('SMTP_PORT_DESCRIP'),
            'EMAIL_PRIORITY': config.FrameworkConfigGet('EMAIL_PRIORITY_DESCRIP'),
            'PDF_TEMPLATE': config.FrameworkConfigGet('PDF_TEMPLATE_DESCRIP'),
            'WORD_TEMPLATE': config.FrameworkConfigGet('WORD_TEMPLATE_DESCRIP'),
            'MSF_LISTENER_IP': config.FrameworkConfigGet('MSF_LISTENER_IP_DESCRIP'),
            'MSF_LISTENER_PORT': config.FrameworkConfigGet('MSF_LISTENER_PORT_DESCRIP'),
            'MSF_LISTENER_SETUP': config.FrameworkConfigGet('MSF_LISTENER_SETUP_DESCRIP'),
            'ATTACHMENT_NAME': config.FrameworkConfigGet('ATTACHMENT_NAME_DESCRIP'),
            'PHISHING_SCRIPT_DIR': config.FrameworkConfigGet('PHISHING_SCRIPT_DIR_DESCRIP')
        },
        'Optional': {
            'PHISHING_CUSTOM_EXE_PAYLOAD_DIR': config.FrameworkConfigGet('PHISHING_CUSTOM_EXE_PAYLOAD_DIR_DESCRIP'),
            'PHISHING_CUSTOM_EXE_PAYLOAD': config.FrameworkConfigGet('PHISHING_CUSTOM_EXE_PAYLOAD_DESCRIP'),
            'ISHELL_EXIT_METHOD': config.FrameworkConfigGet('ISHELL_EXIT_METHOD_DESCRIP'),
            'ISHELL_DELAY_BETWEEN_COMMANDS': config.FrameworkConfigGet('ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT': config.FrameworkConfigGet('ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.FrameworkConfigGet('ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
            'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        # Let user specify the attachment name:
        Args['ATTACHMENT_NAME'] = Args['ATTACHMENT_NAME'] + "_" + Args['PHISHING_PAYLOAD'] + "-" + \
            Args['SET_EMAIL_TEMPLATE']
        plugin_params.SetConfig(Args)  # Only now, after modifying ATTACHMENT_NAME, update config
        Content += ServiceLocator.get_component("spear_phishing").Run(Args, PluginInfo)
    resource = ServiceLocator.get_component("config").GetResources('SendPhishingAttackviaSET')
    Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                         PluginInfo, Content)
    return Content
