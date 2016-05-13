from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Denial of Service (DoS) Launcher -i.e. for IDS/DoS testing-"
CATEGORIES = ['HTTP_WIN', 'HTTP', 'DHCP', 'NTFS', 'HP', 'MDNS', 'PPTP', 'SAMBA', 'SCADA', 'SMTP', 'SOLARIS', 'SSL',
              'SYSLOG', 'TCP', 'WIFI', 'WIN_APPIAN', 'WIN_BROWSER', 'WIN_FTP', 'KAILLERA', 'WIN_LLMNR', 'WIN_NAT',
              'WIN_SMB', 'WIN_SMTP', 'WIN_TFTP', 'WIRESHARK']


def run( PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")
    for Args in plugin_params.GetArgs({
                                                                          'Description': DESCRIPTION,
                                                                          'Mandatory': {
                                                                          'RHOST': config.FrameworkConfigGet('RHOST_DESCRIP'),
                                                                          'RPORT': config.FrameworkConfigGet('RPORT_DESCRIP'),
                                                                          },
                                                                          'Optional': {
                                                                          'CATEGORY': 'Category to use (i.e. ' + ', '.join(
                                                                                  sorted(CATEGORIES)) + ')',
                                                                          'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        plugin_params.SetConfig(Args)
        Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', ServiceLocator.get_component("resource").GetResources('DoS_' + Args['CATEGORY']), PluginInfo, [])  # No previous output

    return Content

