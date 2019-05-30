from owtf.config import config_handler
from owtf.plugin.helper import plugin_helper
from owtf.plugin.params import plugin_params

DESCRIPTION = "Denial of Service (DoS) Launcher -i.e. for IDS/DoS testing-"
CATEGORIES = [
    "HTTP_WIN",
    "HTTP",
    "DHCP",
    "NTFS",
    "HP",
    "MDNS",
    "PPTP",
    "SAMBA",
    "SCADA",
    "SMTP",
    "SOLARIS",
    "SSL",
    "SYSLOG",
    "TCP",
    "WIFI",
    "WIN_APPIAN",
    "WIN_BROWSER",
    "WIN_FTP",
    "KAILLERA",
    "WIN_LLMNR",
    "WIN_NAT",
    "WIN_SMB",
    "WIN_SMTP",
    "WIN_TFTP",
    "WIRESHARK",
]


def run(PluginInfo):
    Content = []
    args = {
        "Description": DESCRIPTION,
        "Mandatory": {
            "RHOST": config_handler.get_val("RHOST_DESCRIP"),
            "RPORT": config_handler.get_val("RPORT_DESCRIP"),
        },
        "Optional": {
            "CATEGORY": "Category to use (i.e. " + ", ".join(sorted(CATEGORIES)) + ")",
            "REPEAT_DELIM": config_handler.get_val("REPEAT_DELIM_DESCRIP"),
        },
    }
    for args in plugin_params.get_args(args, PluginInfo):
        plugin_params.set_config(args)
        resource = config_handler.get_resources("DoS_" + args["CATEGORY"])
        Content += plugin_helper.CommandDump(
            "Test Command", "Output", resource, PluginInfo, ""
        )  # No previous output
    return Content
