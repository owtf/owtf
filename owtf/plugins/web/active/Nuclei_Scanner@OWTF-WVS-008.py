"""
ACTIVE Plugin for Nuclei Vulnerability Scanner
https://github.com/projectdiscovery/nuclei

This plugin demonstrates a modern, self-contained plugin architecture that does NOT
rely on the deprecated plugin_helper or centralized resources.cfg configuration.

Modern Plugin Design Principles:
- Self-contained: All logic in one file
- Direct integration: No resource file lookups
- Structured output: JSON parsing for clean data
- Comprehensive error handling: Graceful failures
- Well documented: Inline comments for maintainability
- Testable: Can be unit tested independently

This pattern can serve as a template for future plugin development and
modernization of existing resource-based plugins.

Tool: Nuclei - Fast vulnerability scanner with 3000+ community templates
Install: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
        or: brew install nuclei
"""
import subprocess
import json
import logging

DESCRIPTION = "Modern template-based vulnerability scanning via Nuclei"

# Plugin output template (imported from OWTF at runtime)
PLUGIN_OUTPUT = {"type": None, "output": None}


def run(PluginInfo):
    """
    Execute Nuclei vulnerability scan against target.
    
    This function demonstrates modern plugin architecture by:
    1. Directly executing the tool (no resource lookups)
    2. Parsing structured JSON output
    3. Handling all error cases gracefully
    4. Providing detailed logging
    5. Returning formatted results for OWTF
    
    Args:
        PluginInfo (dict): OWTF plugin information containing:
            - TARGET: Target URL to scan
            - output_path: Where to store results
            - (other OWTF-specific metadata)
    
    Returns:
        list: OWTF-formatted plugin output with findings
    """
    target = PluginInfo.get("TARGET", "")
    
    if not target:
        logging.error("Nuclei plugin: No target specified")
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "NucleiScan"
        plugin_output["output"] = {
            "status": "error",
            "message": "No target specified"
        }
        return [plugin_output]
    
    logging.info(f"Starting Nuclei scan for target: {target}")
    
    # Step 1: Verify Nuclei is installed
    if not _check_nuclei_installed():
        error_msg = (
            "Nuclei is not installed or not in PATH.\n\n"
            "Installation instructions:\n"
            "  macOS:  brew install nuclei\n"
            "  Linux:  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest\n"
            "  Docker: docker pull projectdiscovery/nuclei:latest\n\n"
            "Documentation: https://docs.projectdiscovery.io/tools/nuclei/install"
        )
        logging.error("Nuclei not found in PATH")
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "NucleiScan"
        plugin_output["output"] = {
            "status": "error",
            "message": error_msg
        }
        return [plugin_output]
    
    # Step 2: Execute Nuclei scan
    scan_results = _execute_nuclei_scan(target)
    
    # Step 3: Format results for OWTF
    return _format_results(scan_results, target, PluginInfo)


def _check_nuclei_installed():
    """
    Verify that Nuclei is installed and accessible.
    
    Returns:
        bool: True if Nuclei is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["nuclei", "-version"],
            capture_output=True,
            timeout=5,
            text=True
        )
        logging.info(f"Nuclei version check: {result.stdout.strip()}")
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        logging.warning("Nuclei version check timed out")
        return False
    except Exception as e:
        logging.error(f"Error checking Nuclei installation: {e}")
        return False


def _execute_nuclei_scan(target):
    """
    Execute Nuclei scan and parse results.
    
    Args:
        target (str): Target URL to scan
    
    Returns:
        dict: Scan results with findings list and metadata
    """
    # Build Nuclei command with optimal settings
    cmd = [
        "nuclei",
        "-u", target,
        "-json",                    # JSON output for parsing
        "-silent",                  # Suppress banner
        "-severity", "critical,high,medium",  # Focus on important findings
        "-timeout", "10",           # Per-template timeout
        "-retries", "1",            # Retry failed templates once
        "-rate-limit", "150",       # Requests per second (be nice to target)
    ]
    
    logging.info(f"Executing: {' '.join(cmd)}")
    
    try:
        # Execute with overall timeout of 10 minutes
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=600,
            text=True,
            check=False  # Don't raise on non-zero exit (Nuclei returns 1 if findings found)
        )
        
        # Parse JSON output
        findings = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    finding = json.loads(line)
                    findings.append(_parse_finding(finding))
                except json.JSONDecodeError as e:
                    logging.debug(f"Failed to parse JSON line: {e}")
                    continue
        
        logging.info(f"Nuclei scan completed: {len(findings)} findings")
        
        return {
            'success': True,
            'findings': findings,
            'total_findings': len(findings),
            'raw_output': result.stdout,
            'stderr': result.stderr if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        logging.error("Nuclei scan timed out after 10 minutes")
        return {
            'success': False,
            'error': 'Scan timed out (10 minute limit)',
            'findings': []
        }
    except Exception as e:
        logging.error(f"Nuclei scan failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'findings': []
        }


def _parse_finding(raw_finding):
    """
    Parse a single Nuclei finding from JSON into clean format.
    
    Args:
        raw_finding (dict): Raw JSON finding from Nuclei
    
    Returns:
        dict: Cleaned and formatted finding
    """
    info = raw_finding.get('info', {})
    
    return {
        'template_id': raw_finding.get('template-id', 'unknown'),
        'name': info.get('name', 'Unknown Vulnerability'),
        'severity': info.get('severity', 'info'),
        'description': info.get('description', ''),
        'reference': info.get('reference', []),
        'tags': info.get('tags', []),
        'matched_at': raw_finding.get('matched-at', ''),
        'matcher_name': raw_finding.get('matcher-name', ''),
        'extracted_results': raw_finding.get('extracted-results', []),
        'curl_command': raw_finding.get('curl-command', '')
    }


def _format_results(scan_results, target, plugin_info):
    """
    Format scan results for OWTF display.
    
    Args:
        scan_results (dict): Results from _execute_nuclei_scan
        target (str): Target URL
        plugin_info (dict): OWTF plugin info
    
    Returns:
        list: OWTF-formatted plugin output
    """
    if not scan_results.get('success'):
        error_msg = scan_results.get('error', 'Unknown error')
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "NucleiScan"
        plugin_output["output"] = {
            "status": "error",
            "message": f"Nuclei scan failed: {error_msg}",
            "target": target
        }
        return [plugin_output]
    
    findings = scan_results.get('findings', [])
    
    # Build formatted text output
    if not findings:
        output_text = f"✓ No vulnerabilities detected for {target}\n\n"
        output_text += "Nuclei scan completed successfully with no findings.\n"
        output_text += "Note: This scanned for critical, high, and medium severity issues only."
    else:
        output_text = f"Nuclei Vulnerability Scan Results for {target}\n"
        output_text += "=" * 80 + "\n\n"
        output_text += f"Total Findings: {len(findings)}\n\n"
        
        # Group by severity
        by_severity = {}
        for finding in findings:
            sev = finding['severity']
            by_severity.setdefault(sev, []).append(finding)
        
        # Display findings grouped by severity
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if severity not in by_severity:
                continue
            
            output_text += f"\n{'='*80}\n"
            output_text += f"{severity.upper()} SEVERITY ({len(by_severity[severity])} findings)\n"
            output_text += f"{'='*80}\n\n"
            
            for idx, finding in enumerate(by_severity[severity], 1):
                output_text += f"{idx}. {finding['name']}\n"
                output_text += f"   Template: {finding['template_id']}\n"
                output_text += f"   Matched: {finding['matched_at']}\n"
                
                if finding['description']:
                    output_text += f"   Description: {finding['description']}\n"
                
                if finding['tags']:
                    output_text += f"   Tags: {', '.join(finding['tags'])}\n"
                
                if finding['reference']:
                    output_text += f"   References:\n"
                    for ref in finding['reference'][:3]:  # Show max 3 refs
                        output_text += f"     - {ref}\n"
                
                output_text += "\n"
    
    # Create OWTF plugin output format
    plugin_output = dict(PLUGIN_OUTPUT)
    plugin_output["type"] = "NucleiScan"
    plugin_output["output"] = {
        "title": "Nuclei Vulnerability Scanner",
        "scan_output": output_text,
        "findings_count": len(findings),
        "severity_breakdown": {
            sev: len(by_severity.get(sev, [])) 
            for sev in ['critical', 'high', 'medium', 'low', 'info']
        }
    }
    
    return [plugin_output]