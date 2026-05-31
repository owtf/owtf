"""
Community Plugin: Nuclei Scanner
---------------------------------
Runs the Nuclei vulnerability scanner against a target URL using
subprocess.run() with a list argument (no shell=True).

This serves as:
  1. A proof of concept that community plugins can match built-in quality.
  2. A reference template for plugin authors.

Plugin structure requirements (enforced by PluginValidator):
  - DESCRIPTION  : module-level string constant
  - ATTR         : dict with group, type, author (optional but recommended)
  - run(target_url) : entry point, returns a JSON-serialisable dict

Return value schema::

    {
        "target": "https://example.com",
        "nuclei_available": true,
        "total_findings": 3,
        "severity_counts": {"critical": 0, "high": 1, "medium": 2, "low": 0, "info": 0},
        "findings": [
            {
                "template_id": "http-missing-security-headers",
                "name": "Missing Security Headers",
                "severity": "medium",
                "matched_at": "https://example.com",
                "description": "..."
            },
            ...
        ],
        "error": null
    }
"""

import json
import subprocess

DESCRIPTION = (
    "Runs the Nuclei vulnerability scanner against the target URL, "
    "parsing JSON output and returning findings mapped to OWTF's format."
)

ATTR = {
    "group": "web",
    "type": "active",
    "author": "owtf-community",
    "version": "1.0.0",
    "tags": "nuclei,scanner,vuln",
    "requires_tool": "nuclei",
}


def _nuclei_available() -> bool:
    """Return True if nuclei binary is on PATH."""
    try:
        result = subprocess.run(
            ["nuclei", "-version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _parse_nuclei_output(raw_stdout: str) -> list:
    """Parse nuclei -json output into a list of finding dicts.

    Nuclei writes one JSON object per line.  Lines that are not valid JSON
    are skipped silently (nuclei sometimes emits progress banners).
    """
    findings = []
    for line in raw_stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        findings.append(
            {
                "template_id": obj.get("template-id", ""),
                "name": obj.get("info", {}).get("name", ""),
                "severity": obj.get("info", {}).get("severity", "info"),
                "matched_at": obj.get("matched-at", ""),
                "description": obj.get("info", {}).get("description", ""),
                "tags": obj.get("info", {}).get("tags", []),
                "reference": obj.get("info", {}).get("reference", []),
                "curl_command": obj.get("curl-command", ""),
            }
        )
    return findings


def run(target_url: str) -> dict:
    """Entry point called by SandboxRunner.

    :param target_url: The URL to scan (must start with http:// or https://)
    :return: JSON-serialisable dict with findings
    """
    error = None
    findings = []

    if not _nuclei_available():
        return {
            "target": target_url,
            "nuclei_available": False,
            "total_findings": 0,
            "severity_counts": {},
            "findings": [],
            "error": (
                "nuclei binary not found on PATH. Install it from https://github.com/projectdiscovery/nuclei/releases"
            ),
        }

    try:
        result = subprocess.run(
            [
                "nuclei",
                "-u",
                target_url,
                "-json",  # machine-readable output
                "-silent",  # suppress banner / progress to stderr
                "-no-color",  # no ANSI codes in output
                "-timeout",
                "10",  # per-request HTTP timeout (seconds)
                "-c",
                "10",  # concurrency (keep it low for community plugins)
            ],
            capture_output=True,
            text=True,
            timeout=280,  # stay under SandboxRunner's default 300s limit
        )
        findings = _parse_nuclei_output(result.stdout)
        if result.returncode not in (0, 1):
            # Exit code 1 = findings found (not an error in nuclei)
            error = result.stderr[:1000] if result.stderr else "nuclei exited with code {}".format(result.returncode)
    except subprocess.TimeoutExpired:
        error = "nuclei scan timed out"
    except Exception as exc:
        error = str(exc)

    severity_counts: dict = {}
    for f in findings:
        sev = f.get("severity", "info").lower()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "target": target_url,
        "nuclei_available": True,
        "total_findings": len(findings),
        "severity_counts": severity_counts,
        "findings": findings,
        "error": error,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OWTF Nuclei Scanner Community Plugin")
    parser.add_argument("--target", required=True, help="Target URL to scan")
    args = parser.parse_args()
    output = run(args.target)
    print(json.dumps(output, indent=2))
