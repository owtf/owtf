"""
ACTIVE Plugin for traightforward testing of email servers for the STARTTLS command injection vulnerability in SMTP, POP3, and IMAP using command-injection-tester.
"""
from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active Vulnerability Scanning of email servers for the STARTTLS command injection vulnerability in SMTP, POP3, and IMAP."


def run(PluginInfo):
    resource = get_resources("IMAP_SMTPinjection")
    return plugin_helper.CommandDump("Test Command", "Output", resource, PluginInfo, [])