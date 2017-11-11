from owtf.dependency_management.dependency_resolver import ServiceLocator
from owtf.lib.general import cprint


DESCRIPTION = "Targeted Phishing Testing plugin"


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'EMAIL_TARGET': config.get_val('EMAIL_TARGET_DESCRIP'),
            'EMAIL_FROM': config.get_val('EMAIL_FROM_DESCRIP'),
            'SMTP_LOGIN': config.get_val('SMTP_LOGIN_DESCRIP'),
            'SMTP_PASS': config.get_val('SMTP_PASS_DESCRIP'),
            'SMTP_HOST': config.get_val('SMTP_HOST_DESCRIP'),
            'SMTP_PORT': config.get_val('SMTP_PORT_DESCRIP'),
            'EMAIL_PRIORITY': config.get_val('EMAIL_PRIORITY_DESCRIP'),
            'EMAIL_SUBJECT': config.get_val('EMAIL_SUBJECT_DESCRIP'),
            'EMAIL_BODY': config.get_val('EMAIL_BODY_DESCRIP'),
        },
        'Optional': {
            'EMAIL_ATTACHMENT': config.get_val('EMAIL_ATTACHMENT_DESCRIP'),
            'REPEAT_DELIM': config.get_val('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(Args)  # Update config
        if ServiceLocator.get_component("smtp").Send(Args):
            cprint("Email delivered succcessfully")
        else:
            cprint("Email delivery failed")
    resource = ServiceLocator.get_component("config").get_resources('SendPhishingAttackviaSET')
    Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                         PluginInfo, Content)
    return Content
