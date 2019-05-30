from owtf.config import config_handler
from owtf.plugin.helper import plugin_helper
from owtf.plugin.params import plugin_params

DESCRIPTION = "Password Bruteforce Testing plugin"
BRUTEFORCER = ["hydra"]
CATEGORIES = [
    "RDP",
    "LDAP2",
    "LDAP3",
    "MSSQL",
    "MYSQL",
    "CISCO",
    "CISCO-ENABLE",
    "CVS",
    "Firebird",
    "FTP",
    "FTPS",
    "HTTP-PROXY",
    "ICQ",
    "IMAP",
    "IRC",
    "NCP",
    "NNTP",
    "ORACLE-LISTENER",
    "ORACLE-SID",
    "PCANYWHERE",
    "PCNFS",
    "POP3",
    "POSTGRES",
    "REXEC",
    "RLOGIN",
    "RSH",
    "SIP",
    "SMB",
    "SMTP",
    "SNMP",
    "SOCKS5",
    "SSH",
    "SVN",
    "TEAMSPEAK",
    "TELNET",
    "VMAUTHD",
    "VNC",
    "XMPP",
]


def run(PluginInfo):
    Content = []
    args = {
        "Description": DESCRIPTION,
        "Mandatory": {
            "RHOST": config_handler.get_val("RHOST_DESCRIP"),
            "RPORT": config_handler.get_val("RPORT_DESCRIP"),
            "CATEGORY": "Category to use (i.e. " + ", ".join(sorted(CATEGORIES)) + ")",
        },
        "Optional": {
            "BRUTEFORCER": "Bruteforcer to use (i.e. "
            + ", ".join(sorted(BRUTEFORCER))
            + ")",
            "ONLINE_USER_LIST": config_handler.get_val("ONLINE_USER_LIST_DESCRIP"),
            "ONLINE_PASSWORD_LIST": config_handler.get_val(
                "ONLINE_PASSWORD_LIST_DESCRIP"
            ),
            "THREADS": config_handler.get_val("THREADS_DESCRIP"),
            "_RESPONSE_WAIT": config_handler.get_val("_RESPONSE_WAIT_DESCRIP"),
            "CONNECT_WAIT": config_handler.get_val("CONNECT_WAIT_DESCRIP"),
            "REPEAT_DELIM": config_handler.get_val("REPEAT_DELIM_DESCRIP"),
        },
    }

    for args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(args)
        resource = config_handler.get_resources(
            "PassBruteForce_" + args["BRUTEFORCER"] + "_" + args["CATEGORY"]
        )
        Content += plugin_helper.CommandDump(
            "Test Command", "Output", resource, PluginInfo, ""
        )  # No previous output
    return Content
