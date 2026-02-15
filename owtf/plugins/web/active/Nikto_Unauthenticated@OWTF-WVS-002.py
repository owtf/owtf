"""
ACTIVE Plugin for Unauthenticated Nikto Testing

This plugin performs comprehensive web server vulnerability scanning using Nikto,
a well-established open-source web server scanner that tests for over 6700
potentially dangerous files/programs, checks for outdated versions of servers,
and tests for version-specific problems.

Nikto performs:
- Comprehensive vulnerability scanning
- Server version detection and CVE checking
- Dangerous file/program detection
- Configuration issue identification
- Default credential testing
- Common misconfiguration checks

Note: This is an ACTIVE plugin that sends numerous requests to the target server.
Ensure you have proper authorization before running. Scans typically take 5-15
minutes depending on target size and response times.

Tool: Nikto (https://github.com/sullo/nikto)
"""
import logging

from owtf.managers.resource import get_resources
from owtf.plugin.helper import plugin_helper

DESCRIPTION = "Active Vulnerability Scanning without credentials via nikto"


def run(PluginInfo):
    """
    Execute Nikto vulnerability scan against target web server.
    
    This function performs two scan phases:
    1. Primary Nikto scan - Comprehensive vulnerability detection
    2. Verification scan - Detailed analysis with direct links to findings
    
    The verification results are displayed first as they contain more useful
    information including clickable links to vulnerabilities found.
    
    Args:
        PluginInfo (dict): OWTF plugin information containing:
            - TARGET: Target URL to scan
            - output_path: Directory for storing results
            - (additional OWTF metadata)
    
    Returns:
        list: Combined output from verification and primary scans,
              formatted for OWTF web interface display.
              Returns verification results first, followed by raw scan output.
    """
    target = PluginInfo.get("TARGET", "Unknown")
    
    logging.info(f"Starting Nikto vulnerability scan for target: {target}")
    logging.info("Nikto scan may take 5-15 minutes depending on target complexity")
    
    # Phase 1: Execute primary Nikto comprehensive scan
    logging.info("Phase 1: Executing primary Nikto vulnerability scan")
    NiktoOutput = plugin_helper.CommandDump(
        "Nikto Comprehensive Scan",
        "Complete Nikto vulnerability scan output including all findings",
        get_resources("Nikto_Unauth"),
        PluginInfo,
        []
    )
    
    # Phase 2: Execute verification scan for detailed analysis
    logging.info("Phase 2: Executing Nikto verification and analysis")
    Content = plugin_helper.CommandDump(
        "Nikto Findings Verification",
        "Detailed verification and analysis of Nikto findings with direct links",
        get_resources("Nikto_Verify_Unauth"),
        PluginInfo,
        NiktoOutput,
    )
    
    logging.info(f"Nikto scan completed successfully for {target}")
    
    # Return verification results first (more useful - contains links to findings)
    # followed by raw scan output for reference
    return Content + NiktoOutput