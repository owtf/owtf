from owtf.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Denial of Service (DoS) Launcher -i.e. for IDS/DoS testing-"
CATEGORIES = ['HTTP_WIN', 'HTTP', 'DHCP', 'NTFS', 'HP', 'MDNS', 'PPTP', 'SAMBA', 'SCADA', 'SMTP', 'SOLARIS', 'SSL',
              'SYSLOG', 'TCP', 'WIFI', 'WIN_APPIAN', 'WIN_BROWSER', 'WIN_FTP', 'KAILLERA', 'WIN_LLMNR', 'WIN_NAT',
              'WIN_SMB', 'WIN_SMTP', 'WIN_TFTP', 'WIRESHARK']


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'RHOST': config.get_val('RHOST_DESCRIP'),
            'RPORT': config.get_val('RPORT_DESCRIP')
        },
        'Optional': {
            'CATEGORY': 'Category to use (i.e. ' + ', '.join(sorted(CATEGORIES)) + ')',
            'REPEAT_DELIM': config.get_val('REPEAT_DELIM_DESCRIP')
        }
    }
    for Args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(Args)
        resource = config.get_resources('DoS_' + Args['CATEGORY'])
        Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                             PluginInfo, "")  # No previous output
    return Content
