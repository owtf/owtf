from framework.dependency_management.dependency_resolver import ServiceLocator

DESCRIPTION = "Password Bruteforce Testing plugin"
BRUTEFORCER = ['hydra']
CATEGORIES = ['RDP', 'LDAP2', 'LDAP3', 'MSSQL', 'MYSQL', 'CISCO', 'CISCO-ENABLE', 'CVS', 'Firebird', 'FTP', 'FTPS',
              'HTTP-PROXY', 'ICQ', 'IMAP', 'IRC', 'NCP', 'NNTP', 'ORACLE-LISTENER', 'ORACLE-SID', 'PCANYWHERE', 'PCNFS',
              'POP3', 'POSTGRES', 'REXEC', 'RLOGIN', 'RSH', 'SIP', 'SMB', 'SMTP', 'SNMP', 'SOCKS5', 'SSH', 'SVN',
              'TEAMSPEAK', 'TELNET', 'VMAUTHD', 'VNC', 'XMPP']


def run( PluginInfo):
    # ServiceLocator.get_component("config").Show()
    Content = DESCRIPTION + " Results:<br />"
    config = ServiceLocator.get_component("config")
    for Args in ServiceLocator.get_component("plugin_params").GetArgs({
                                                                          'Description': DESCRIPTION,
                                                                          'Mandatory': {
                                                                              'RHOST': config.Get('RHOST_DESCRIP'),
                                                                              'RPORT': config.Get('RPORT_DESCRIP'),
                                                                              'CATEGORY': 'Category to use (i.e. ' + ', '.join(
                                                                                      sorted(CATEGORIES)) + ')'
                                                                          },
                                                                          'Optional': {
                                                                              'BRUTEFORCER': 'Bruteforcer to use (i.e. ' + ', '.join(
                                                                                      sorted(BRUTEFORCER)) + ')',
                                                                              'ONLINE_USER_LIST': config.Get(
                                                                                      'ONLINE_USER_LIST_DESCRIP'),
                                                                              'ONLINE_PASSWORD_LIST': config.Get(
                                                                                      'ONLINE_PASSWORD_LIST_DESCRIP'),
                                                                              'THREADS': config.Get('THREADS_DESCRIP'),
                                                                              'RESPONSE_WAIT': config.Get(
                                                                                      'RESPONSE_WAIT_DESCRIP'),
                                                                              'CONNECT_WAIT': config.Get(
                                                                                      'CONNECT_WAIT_DESCRIP'),
                                                                              'REPEAT_DELIM': config.Get(
                                                                                      'REPEAT_DELIM_DESCRIP')
                                                                          }}, PluginInfo):
        ServiceLocator.get_component("plugin_params").SetConfig(Args)
    # print "Args="+str(Args)
    Content += ServiceLocator.get_component("plugin_helper").DrawCommandDump('Test Command', 'Output',
                                                                             config.GetResources(
                                                                                 'PassBruteForce_' + Args[
                                                                                     'BRUTEFORCER'] + "_" + Args[
                                                                                     'CATEGORY']), PluginInfo,
                                                                             "")  # No previous output
    return Content

