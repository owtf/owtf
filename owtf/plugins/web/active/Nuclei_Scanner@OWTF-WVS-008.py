"""
ACTIVE Plugin for Nuclei Vulnerability Scanner
https://github.com/projectdiscovery/nuclei

Modern self-contained plugin - no plugin_helper or resources.cfg dependency.

Tool: Nuclei - Fast vulnerability scanner with community templates
Install: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
        or: brew install nuclei
"""
import subprocess
import json
import logging

from owtf.managers.target import target_manager

DESCRIPTION = "Modern template-based vulnerability scanning via Nuclei"

PLUGIN_OUTPUT = {"type": "CommandDump", "output": {}}


def run(PluginInfo):
    """
    Execute Nuclei vulnerability scan against the current target.

    Gets target URL from OWTF's target_manager (the correct way to access
    the current target in OWTF plugins, not from PluginInfo directly).

    Args:
        PluginInfo (dict): OWTF plugin metadata passed by the runner.

    Returns:
        list: OWTF-compatible plugin output with ResourceList for UI rendering.
    """
    target = target_manager.get_val("target_url")

    if not target:
        logging.error("Nuclei plugin: Could not retrieve target URL from target_manager")
        return _error_output("Could not retrieve target URL")

    logging.info("Starting Nuclei scan for target: %s", target)

    if not _check_nuclei_installed():
        msg = (
            "Nuclei is not installed or not in PATH.\n\n"
            "Install instructions:\n"
            "  macOS:  brew install nuclei\n"
            "  Linux:  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest\n"
            "  Docs:   https://docs.projectdiscovery.io/tools/nuclei/install"
        )
        logging.error("Nuclei not found in PATH")
        return _error_output(msg)

    scan_results = _execute_nuclei_scan(target)
    return _format_results(scan_results, target)


def _check_nuclei_installed():
    """Check if nuclei binary is available in PATH."""
    try:
        result = subprocess.run(
            ["nuclei", "-version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        logging.warning("Nuclei version check timed out")
        return False
    except Exception as e:
        logging.error("Error checking Nuclei installation: %s", e)
        return False


def _execute_nuclei_scan(target):
    """
    Run nuclei against the target and return parsed findings.

    Args:
        target (str): Target URL to scan.

    Returns:
        dict: findings list and success/error status.
    """
    cmd = [
        "nuclei",
        "-u", target,
        "-json",
        "-silent",
        "-severity", "critical,high,medium",
        "-timeout", "10",
        "-retries", "1",
        "-rate-limit", "150",
    ]

    logging.info("Executing: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,
            text=True,
            check=False
        )

        findings = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                try:
                    findings.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        logging.info("Nuclei scan completed: %d findings", len(findings))
        return {"success": True, "findings": findings}

    except subprocess.TimeoutExpired:
        logging.error("Nuclei scan timed out after 10 minutes")
        return {"success": False, "error": "Scan timed out (10 minute limit)", "findings": []}
    except Exception as e:
        logging.error("Nuclei scan failed: %s", e)
        return {"success": False, "error": str(e), "findings": []}


def _format_results(scan_results, target):
    """
    Format scan results as OWTF ResourceList for web UI rendering.

    The OWTF frontend (Table.tsx) renders plugin output by reading
    ResourceList (list of [label, url] pairs) and ResourceListName.
    This is the only output structure the UI displays.

    Args:
        scan_results (dict): Results from _execute_nuclei_scan.
        target (str): Target URL that was scanned.

    Returns:
        list: OWTF plugin output list.
    """
    if not scan_results.get("success"):
        error = scan_results.get("error", "Unknown error")
        return _error_output("Nuclei scan failed: {}".format(error))

    findings = scan_results.get("findings", [])

    if not findings:
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["output"] = {
            "ResourceListName": "Nuclei Scan: {}".format(target),
            "ResourceList": [
                ["No vulnerabilities found (critical/high/medium)", target]
            ]
        }
        return [plugin_output]

    # Build ResourceList from findings sorted by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.get(
            f.get("info", {}).get("severity", "info"), 4
        )
    )

    resource_list = []
    for finding in sorted_findings:
        info = finding.get("info", {})
        severity = info.get("severity", "info").upper()
        name = info.get("name", "Unknown")
        matched_at = finding.get("matched-at", target)
        template_id = finding.get("template-id", "")

        # Label: [SEVERITY] Name (template-id) -> links to matched URL
        label = "[{}] {} ({})".format(severity, name, template_id)
        resource_list.append([label, matched_at])

    plugin_output = dict(PLUGIN_OUTPUT)
    plugin_output["output"] = {
        "ResourceListName": "Nuclei Findings for {} ({} total)".format(
            target, len(findings)
        ),
        "ResourceList": resource_list
    }
    return [plugin_output]


def _error_output(message):
    """Return a standardised error output renderable by the OWTF UI."""
    plugin_output = dict(PLUGIN_OUTPUT)
    plugin_output["output"] = {
        "ResourceListName": "Nuclei Scanner - Error",
        "ResourceList": [
            [message, "#"]
        ]
    }
    return [plugin_output]
