from framework.dependency_management.dependency_resolver import ServiceLocator


DESCRIPTION = "Password Bruteforce Testing plugin"
BRUTEFORCER = ['hydra']
CATEGORIES = ['RDP', 'LDAP2', 'LDAP3', 'MSSQL', 'MYSQL', 'CISCO', 'CISCO-ENABLE', 'CVS', 'Firebird', 'FTP', 'FTPS',
              'HTTP-PROXY', 'ICQ', 'IMAP', 'IRC', 'NCP', 'NNTP', 'ORACLE-LISTENER', 'ORACLE-SID', 'PCANYWHERE', 'PCNFS',
              'POP3', 'POSTGRES', 'REXEC', 'RLOGIN', 'RSH', 'SIP', 'SMB', 'SMTP', 'SNMP', 'SOCKS5', 'SSH', 'SVN',
              'TEAMSPEAK', 'TELNET', 'VMAUTHD', 'VNC', 'XMPP']


def run(PluginInfo):
    Content = []
    plugin_params = ServiceLocator.get_component("plugin_params")
    config = ServiceLocator.get_component("config")

    args = {
        'Description': DESCRIPTION,
        'Mandatory': {
            'RHOST': config.FrameworkConfigGet('RHOST_DESCRIP'),
            'RPORT': config.FrameworkConfigGet('RPORT_DESCRIP'),
            'CATEGORY': 'Category to use (i.e. ' + ', '.join(sorted(CATEGORIES)) + ')'
        },
        'Optional': {
            'BRUTEFORCER': 'Bruteforcer to use (i.e. ' + ', '.join(sorted(BRUTEFORCER)) + ')',
            'ONLINE_USER_LIST': config.FrameworkConfigGet('ONLINE_USER_LIST_DESCRIP'),
            'ONLINE_PASSWORD_LIST': config.FrameworkConfigGet('ONLINE_PASSWORD_LIST_DESCRIP'),
            'THREADS': config.FrameworkConfigGet('THREADS_DESCRIP'),
            '_RESPONSE_WAIT': config.FrameworkConfigGet('_RESPONSE_WAIT_DESCRIP'),
            'CONNECT_WAIT': config.FrameworkConfigGet('CONNECT_WAIT_DESCRIP'),
            'REPEAT_DELIM': config.FrameworkConfigGet('REPEAT_DELIM_DESCRIP')
        }
    }

    for Args in plugin_params.GetArgs(args, PluginInfo):
        plugin_params.SetConfig(Args)
        resource = config.GetResources('PassBruteForce_' + Args['BRUTEFORCER'] + "_" + Args['CATEGORY'])
        Content += ServiceLocator.get_component("plugin_helper").CommandDump('Test Command', 'Output', resource,
                                                                             PluginInfo, "")  # No previous output
    return Content
