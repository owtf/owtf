from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Spear Phishing Testing plugin"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'EMAIL_TARGET': config.get_val('EMAIL_TARGET_DESCRIP'),
            'EMAIL_FROM': config.get_val('EMAIL_FROM_DESCRIP'),
            'PHISHING_PAYLOAD': config.get_val('PHISHING_PAYLOAD_DESCRIP'),
            'SET_FILE_EXTENSION_ATTACK': config.get_val('SET_FILE_EXTENSION_ATTACK_DESCRIP'),
            'SET_EMAIL_TEMPLATE': config.get_val('SET_EMAIL_TEMPLATE_DESCRIP'),
            'SMTP_LOGIN': config.get_val('SMTP_LOGIN_DESCRIP'),
            'SMTP_PASS': config.get_val('SMTP_PASS_DESCRIP'),
            'SMTP_HOST': config.get_val('SMTP_HOST_DESCRIP'),
            'SMTP_PORT': config.get_val('SMTP_PORT_DESCRIP'),
            'EMAIL_PRIORITY': config.get_val('EMAIL_PRIORITY_DESCRIP'),
            'PDF_TEMPLATE': config.get_val('PDF_TEMPLATE_DESCRIP'),
            'WORD_TEMPLATE': config.get_val('WORD_TEMPLATE_DESCRIP'),
            'MSF_LISTENER_IP': config.get_val('MSF_LISTENER_IP_DESCRIP'),
            'MSF_LISTENER_PORT': config.get_val('MSF_LISTENER_PORT_DESCRIP'),
            'MSF_LISTENER_SETUP': config.get_val('MSF_LISTENER_SETUP_DESCRIP'),
            'ATTACHMENT_NAME': config.get_val('ATTACHMENT_NAME_DESCRIP'),
            'PHISHING_SCRIPT_DIR': config.get_val('PHISHING_SCRIPT_DIR_DESCRIP')
        },
        'Optional': {
            'PHISHING_CUSTOM_EXE_PAYLOAD_DIR': config.get_val('PHISHING_CUSTOM_EXE_PAYLOAD_DIR_DESCRIP'),
            'PHISHING_CUSTOM_EXE_PAYLOAD': config.get_val('PHISHING_CUSTOM_EXE_PAYLOAD_DESCRIP'),
            'ISHELL_EXIT_METHOD': config.get_val('ISHELL_EXIT_METHOD_DESCRIP'),
            'ISHELL_DELAY_BETWEEN_COMMANDS': config.get_val('ISHELL_DELAY_BETWEEN_COMMANDS_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT': config.get_val('ISHELL_COMMANDS_BEFORE_EXIT_DESCRIP'),
            'ISHELL_COMMANDS_BEFORE_EXIT_DELIM': config.get_val('ISHELL_COMMANDS_BEFORE_EXIT_DELIM_DESCRIP'),
            'REPEAT_DELIM': config.get_val('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.get_args(args, PluginInfo):
        # Let user specify the attachment name:
        Args['ATTACHMENT_NAME'] = Args['ATTACHMENT_NAME'] + "_" + Args['PHISHING_PAYLOAD'] + "-" + \
            Args['SET_EMAIL_TEMPLATE']
        plugin_params.set_config(Args)  # Only now, after modifying ATTACHMENT_NAME, update config
        Content += ServiceLocator.get_component("spear_phishing").run(Args, PluginInfo)
    resource = ServiceLocator.get_component("config").get_resources('SendPhishingAttackviaSET')
    Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                         PluginInfo, Content)
    return Content
