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
            'EMAIL_TARGET': config.FrameworkConfigGet('EMAIL_TARGET_DESCRIP'),
            'EMAIL_FROM': config.FrameworkConfigGet('EMAIL_FROM_DESCRIP'),
            'SMTP_LOGIN': config.FrameworkConfigGet('SMTP_LOGIN_DESCRIP'),
            'SMTP_PASS': config.FrameworkConfigGet('SMTP_PASS_DESCRIP'),
            'SMTP_HOST': config.FrameworkConfigGet('SMTP_HOST_DESCRIP'),
            'SMTP_PORT': config.FrameworkConfigGet('SMTP_PORT_DESCRIP'),
            'EMAIL_PRIORITY': config.FrameworkConfigGet('EMAIL_PRIORITY_DESCRIP'),
            'EMAIL_SUBJECT': config.FrameworkConfigGet('EMAIL_SUBJECT_DESCRIP'),
            'EMAIL_BODY': config.FrameworkConfigGet('EMAIL_BODY_DESCRIP'),
        },
        'Optional': {
            'EMAIL_ATTACHMENT': config.FrameworkConfigGet('EMAIL_ATTACHMENT_DESCRIP'),
            'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)  # Update config
        if ServiceLocator.get_component("smtp").Send(Args):
            cprint("Email delivered succcessfully")
        else:
            cprint("Email delivery failed")
    resource = ServiceLocator.get_component("config").get_resources('SendPhishingAttackviaSET')
    Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                         PluginInfo, Content)
    return Content
