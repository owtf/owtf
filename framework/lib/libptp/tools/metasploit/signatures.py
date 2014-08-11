"""

    Metasploit does not provide ranking for the vulnerabilities it has found.
    This file tries to define a ranking for every Metasploit's modules
    discoveries it might find.

"""


from framework.lib.libptp.constants import HIGH, MEDIUM, LOW, INFO


# TODO: Complete the signatures database.
SIGNATURES = {
    # Metasploit's scanner modules.
    'auxiliary/scanner/ftp/anonymous': {
        'Anonymous READ/WRITE ': HIGH,
        'Anonymous READ ': LOW,
        },

    'auxiliary/scanner/ftp/ftp_version': {
        'FTP Banner': INFO,
        },

    'auxiliary/scanner/ftp/ftp_login': {
        'has READ/WRITE access': HIGH,
        'has READ access': LOW,
        },

    'auxiliary/scanner/smtp/smtp_enum': {
        'Found user': LOW,
        'Users found': LOW,
        },

    'auxiliary/scanner/smtp/smtp_version': {
        'SMTP': INFO,
        },

    'auxiliary/scanner/vnc/vnc_login': {
        'VNC server password': HIGH,
        },

    'auxiliary/scanner/vnc/vnc_none_auth': {
        'free access': HIGH,
        },

    'auxiliary/scanner/x11/open_x11': {
        'Open X Server': HIGH,
        },

    'auxiliary/scanner/emc/alphastor_devicemanager': {
        'is running the EMC AlphaStor Device Manager': INFO,
        },

    'auxiliary/scanner/emc/alphastor_librarymanager': {
        'is running the EMC AlphaStor Library Manager': INFO,
        },

    'auxiliary/scanner/mssql/mssql_ping': {
        'SQL Server information for': INFO,
        },

    'auxiliary/scanner/mssql/mssql_login': {
        'MSSQL - successful login': HIGH,
        'successful logged in as': HIGH,
        },

    # TODO: Enhance the matching string.
    'auxiliary/scanner/mssql/mssql_hashdump': {
        'Saving': HIGH,
        },

    'auxiliary/scanner/mssql/mssql_schemadump': {
        'Microsoft SQL Server Schema': HIGH,
        },

    # TODO: Complete the matching strings.
    'auxiliary/scanner/dcerpc/management': {
        },

    'auxiliary/scanner/dcerpc/endpoint_mapper': {
        'Endpoint Mapper': INFO,
        },

    'auxiliary/scanner/dcerpc/hidden': {
        'HIDDEN: UUID': INFO,
        },

    'auxiliary/scanner/smb/smb_version': {
        'is running': INFO,
        },

    'auxiliary/scanner/smb/pipe_auditor': {
        '- Pipes:': INFO,
        },

    # TODO: Enhance the matching string (using regexp IMO).
    'auxiliary/scanner/smb/smb_enumusers': {
        ', ': INFO,
        },

    'auxiliary/scanner/smb/smb_login': {
        'SUCCESSFUL LOGIN': HIGH,
        },

    'auxiliary/scanner/snmp/snmp_enumusers': {
        'Found Users': LOW,
        },

    # FIXME: when the connection is refused, the report contains the following
    # string: "The unit tests of metasploit are not complete." which matches
    # the " - " signature string.
    #'auxiliary/scanner/snmp/snmp_enumshares': {
    #    ' - ': LOW,
    #    },

    'auxiliary/scanner/snmp/snmp_enum': {
        ', Connected.': INFO,
        },

    'auxiliary/scanner/snmp/aix_version': {
        'IBM AIX Version': INFO,
        },

    'auxiliary/scanner/snmp/snmp_login': {
        'community string': LOW,
        'provides READ-ONLY access': LOW,
        'provides READ-WRITE access': HIGH,
        },

    # Metasploit's fuzzer modules.
    # TODO: Complete the matching strings.
    'auxiliary/fuzzers/smtp/smtp_fuzzer': {
        },

    # Metasploit's DoS modules.
    'auxiliary/dos/windows/http/ms10_065_ii6_asp_dos': {
        'IIS should now be unavailable': HIGH,
        },

    'auxiliary/dos/http/3com_superstack_switch': {
        'DoS packet successful.': HIGH,
        },

    'auxiliary/dos/http/apache_range_dos': {
        'Found Byte-Range Header DOS at': HIGH,
        },

    'auxiliary/dos/http/apache_tomcat_transfer_encoding': {
        'DoS packet successful.': HIGH,
        },

    'auxiliary/dos/samba/lsa_addprivs_heap': {
        'Server did not respond, this is expected': HIGH,
        'Server disconnected, this is expected': HIGH,
        },

    'auxiliary/dos/samba/lsa_transnames_heap': {
        'Server did not respond, this is expected': HIGH,
        'Server disconnected, this is expected': HIGH,
        },

    'auxiliary/dos/smtp/sendmail_prescan': {
        'target vulnerable.': HIGH,
        },

    'auxiliary/dos/solaris/lpd/cascade_delete': {
        'Successfully deleted': HIGH,
        },

    'auxiliary/dos/windows/ftp/iis_list_exhaustion': {
        'Success! Service is down': HIGH,
        },

    'auxiliary/dos/windows/games/kaillera': {
        'Target is down': HIGH,
        },

    'auxiliary/dos/windows/smb/ms05_047_pnp': {
        'Server did not respond, this is expected': HIGH,
        'Connection reset by peer (possible success)': HIGH,
        'Server disconnected, this is expected': HIGH,
        },

    'auxiliary/dos/windows/smb/ms09_050_smb2_negotiate_pidhigh': {
        'The target system has likely crashed': HIGH,
        },

    'auxiliary/dos/windows/smb/ms09_050_smb2_session_logoff': {
        'No response. The target system has probably crashed.': HIGH,
        },

    # Metasploit's Exploit modules.
    'exploit/dialup/multi/login/manyargs': {
        'Success!!!': HIGH,
        },

    'exploit/linux/games/ut2004_secure': {
        'This system appears to be exploitable': HIGH,
        },

    'exploit/linux/http/piranha_passwd_exec': {
        'Command successfully executed (according to the server).': HIGH,
        },

    'exploit/linux/samba/lsa_transnames_heap': {
        'Server did not respond, this is expected': HIGH,
        'Server disconnected, this is expected': HIGH,
        },

    'exploit/multi/ftp/wuftpd_site_exec_format': {
        'Your payload should have executed now': HIGH,
        },

    'exploit/multi/http/freenas_exec_raw': {
        'Triggering payload...': HIGH,
        },

    'exploit/multi/http/glassfish_deployer': {
        'GlassFish - SUCCESSFUL login for': HIGH,
        },

    'exploit/multi/http/jboss_deploymentfilerepository': {
        'Successfully called': HIGH,
        },

    'exploit/multi/http/jboss_maindeployer': {
        'Successfully triggered payload at': HIGH,
        },

    'exploit/multi/http/sit_file_upload': {
        'Successfully': HIGH,
        },

    'exploit/multi/misc/java_rmi_server': {
        'may be exploitable...': HIGH,
        },

    'exploit/multi/misc/openview_omniback_exec': {
        'The remote service is exploitable': HIGH,
        },

    'exploit/multi/php/php_unserialize_zval_cookie': {
        'The server runs a vulnerable version of PHP': HIGH,
        },

    'exploit/solaris/lpd/sendmail_exec': {
        'Uploaded': HIGH,
        },

    'exploit/solaris/sunrpc/sadmind_exec': {
        'exploit did not give us an error, this is good...': HIGH,
        },

    'exploit/unix/ftp/vsftpd_234_backdoor': {
        'Backdoor service has been spawned, handling...': HIGH,
        },

    'exploit/unix/http/contentkeeperweb_mimencode': {
        'Privilege escalation appears to have worked!': HIGH,
        },

    'exploit/unix/misc/zabbix_agent_exec': {
        'The zabbix agent should have executed our command.': HIGH,
        },

    'exploit/unix/smtp/exim4_string_format': {
        'Payload result:': HIGH,
        'Perl binary detected, attempt to escalate...': HIGH,
        },

    'exploit/unix/webapp/awstats_configdir_exec': {
        'Command output from the server:': HIGH,
        },

    'exploit/unix/webapp/awstats_migrate_exec': {
        'Command output from the server:': HIGH,
        },

    'exploit/unix/webapp/awstatstotals_multisort': {
        'Command output from the server:': HIGH,
        },

    'exploit/unix/webapp/barracuda_img_exec': {
        'Command output from the server:': HIGH,
        },

    'exploit/unix/webapp/cacti_graphimage_exec': {
        'Command output from the server:': HIGH,
        },

    'exploit/unix/webapp/coppermine_piceditor': {
        "Successfully POST'd exploit data": HIGH,
        },

    'exploit/unix/webapp/google_proxystylesheet_exec': {
        'This system appears to be vulnerable': HIGH,
        },

    'exploit/unix/webapp/nagios3_statuswml_ping': {
        'Session created, enjoy!': HIGH,
        },

    'exploit/unix/webapp/openview_connectednodes_exec': {
        'Command output from the server:': HIGH,
        },

    'exploit/unix/webapp/openx_banner_edit': {
        'Successfully deleted banner': MEDIUM,
        },

    'exploit/unix/webapp/oracle_vm_agent_utl': {
        'Our request was accepted!': HIGH,
        },

    'exploit/unix/webapp/php_vbulletin_template': {
        'exploit successful': MEDIUM,
        'Command returned': MEDIUM,
        },

    'exploit/unix/webapp/php_xmlrpc_eval': {
        'exploit successful': MEDIUM,
        'Command returned': MEDIUM,
        },

    'exploit/unix/webapp/sphpblog_file_upload': {
        'Successfully': HIGH,
        },

    'exploit/unix/webapp/tikiwiki_graph_formula_exec': {
        'TikiWiki database informations': HIGH,
        },

    'exploit/unix/webapp/tikiwiki_jhot_exec': {
        'Successfully': HIGH,
        'Command output from the server :': HIGH,
        },

    'exploit/unix/webapp/twiki_history': {
        'Successfully sent exploit request': HIGH,
        },

    'exploit/unix/webapp/twiki_search': {
        'Successfully sent exploit request': HIGH,
        },

    'exploit/windows/antivirus/ams_xfr': {
        'Got data, execution successful!': HIGH,
        },

    'exploit/windows/games/ut2004_secure': {
        'This system appears to be exploitable': HIGH,
        'This system appears to be running UT2003': MEDIUM,
        },

    'exploit/windows/iis/ms01_026_dbldecode': {
        'Command output': HIGH,
        },

    'exploit/windows/iis/ms03_007_ntdll_webdav': {
        'The server stopped accepting requests': HIGH,
        },

    'exploit/windows/license/calicserv_getconfig': {
        'CA License Server reports OS': HIGH,
        },

    'exploit/windows/misc/bakbone_netvault_heap': {
        'Detected NetVault Build': HIGH,
        },

    'exploit/windows/mssql/lyris_listmanager_weak_pass': {
        'Successfully authenticated to': HIGH,
        },

    'exploit/windows/postgres/postgres_payload': {
        'Authentication successful.': HIGH,
        },

    'exploit/windows/smtp/ypops_overflow1': {
        'Vulnerable SMTP server': HIGH,
        },

    'exploit/windows/ssh/freeftpd_key_exchange': {
        'Trying target': HIGH,
        },

    'exploit/windows/ssh/freesshd_key_exchange': {
        'Trying target': HIGH,
        },
}
