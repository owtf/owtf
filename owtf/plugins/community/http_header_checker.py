"""
Community Plugin: HTTP Security Header Checker
----------------------------------------------
Checks a target URL for missing or misconfigured HTTP security headers.
Uses curl via subprocess (no shell=True) with urllib as fallback.

This is the simplest possible reference plugin. No external scanner required.
"""

import json
import subprocess
import urllib.error
import urllib.request

DESCRIPTION = (
    "Checks the target for missing HTTP security headers "
    "(HSTS, CSP, X-Frame-Options, etc.) and reports their presence or absence."
)

ATTR = {
    "group": "web",
    "type": "passive",
    "author": "owtf-community",
    "version": "1.0.0",
    "tags": "headers,passive,security",
}

SECURITY_HEADERS = {
    "Strict-Transport-Security": "Prevents protocol downgrade attacks (HSTS)",
    "X-Frame-Options": "Prevents clickjacking",
    "X-Content-Type-Options": "Prevents MIME-type sniffing",
    "Content-Security-Policy": "Controls allowed resource origins (CSP)",
    "Referrer-Policy": "Controls referrer information leakage",
    "Permissions-Policy": "Controls browser feature access",
    "X-XSS-Protection": "Legacy XSS filter (supplementary to CSP)",
}


def _fetch_headers_curl(target_url: str) -> dict:
    result = subprocess.run(
        ["curl", "-sI", "--max-time", "10", "--location", target_url],
        capture_output=True,
        text=True,
        timeout=15,
    )
    headers = {}
    for line in result.stdout.splitlines()[1:]:
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
    return headers


def _fetch_headers_urllib(target_url: str) -> dict:
    req = urllib.request.Request(
        target_url,
        headers={"User-Agent": "OWTF-Community-Plugin/1.0"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return {k.lower(): v for k, v in dict(resp.headers).items()}


def run(PluginInfo) -> dict:
    """Entry point invoked by the OWTF plugin runner.

    ``PluginInfo`` is the standard plugin dict; ``target_url`` is taken
    from ``PluginInfo["target_url"]`` when present, otherwise from the
    target manager.
    """
    if isinstance(PluginInfo, dict):
        target_url = PluginInfo.get("target_url")
        if not target_url:
            from owtf.managers.target import target_manager

            target_url = target_manager.get_target_url()
    else:
        target_url = PluginInfo

    raw_headers = {}
    fetch_method = "unknown"
    error = None

    try:
        try:
            raw_headers = _fetch_headers_curl(target_url)
            fetch_method = "curl"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            raw_headers = _fetch_headers_urllib(target_url)
            fetch_method = "urllib"
    except Exception as exc:
        error = str(exc)

    findings = []
    for header, explanation in SECURITY_HEADERS.items():
        if header.lower() in raw_headers:
            findings.append(
                {
                    "header": header,
                    "severity": "info",
                    "status": "present",
                    "value": raw_headers[header.lower()],
                    "description": explanation,
                }
            )
        else:
            findings.append(
                {
                    "header": header,
                    "severity": "medium",
                    "status": "missing",
                    "value": None,
                    "description": explanation,
                }
            )

    missing_count = sum(1 for f in findings if f["status"] == "missing")

    return {
        "target": target_url,
        "fetch_method": fetch_method,
        "total_headers_checked": len(SECURITY_HEADERS),
        "missing_count": missing_count,
        "findings": findings,
        "error": error,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Target URL")
    args = parser.parse_args()
    print(json.dumps(run({"target_url": args.target}), indent=2))
