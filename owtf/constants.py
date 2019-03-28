"""
owtf.constants
~~~~~~~~~~~~~~

Ranking constants used across the framework.
"""

# `int` value of ranks
OWTF_UNRANKED = -1
OWTF_PASSING = 0
OWTF_INFO = 1
OWTF_LOW = 2
OWTF_MEDIUM = 3
OWTF_HIGH = 4
OWTF_CRITICAL = 5

# Maps `int` value of ranks with `string` value.
RANKS = {
    OWTF_UNRANKED: "Unranked",
    OWTF_PASSING: "Passing",
    OWTF_INFO: "Informational",
    OWTF_LOW: "Low",
    OWTF_MEDIUM: "Medium",
    OWTF_HIGH: "High",
    OWTF_CRITICAL: "Critical",
}

SUPPORTED_MAPPINGS = ["OWASP_V3", "OWASP_V4", "NIST", "OWASP_TOP_10", "CWE"]

MAPPINGS = {
    "OWTF-IG-001": {
        "OWASP_V3": ["OWASP-IG-001", "Spiders Robots and Crawlers"],
        "OWASP_V4": [
            "OTF-INFO-003", "Review Webserver Metafiles for Information Leakage"
        ],
        "NIST": ["AU-13", "Monitoring for Information Disclosure - Spider, Robots"],
        "OWASP_TOP_10": ["A6", "Sensitive Data Exposure - Spider, Robots"],
        "CWE": [
            "CWE-312", "Cleartext Storage of Sensitive Information - Spider, Robots"
        ],
    },
    "OWTF-IG-002": {
        "OWASP_V3": ["OWASP-IG-002", "Search Engine Discovery/Reconnaissance"],
        "OWASP_V4": [
            "OTG-INFO-001", "Conduct Search Engine Discovery and Reconnaissance"
        ],
        "NIST": ["AU-13", "Monitoring for Information Disclosure - Search Engine"],
        "OWASP_TOP_10": ["A6", "Sensitive Data Exposure - Search Engine"],
        "CWE": [
            "CWE-312", "Cleartext Storage of Sensitive Information - Search Engine"
        ],
    },
    "OWTF-IG-003": {
        "OWASP_V3": ["OWASP-IG-003", "Identify application entry points"],
        "OWASP_V4": ["OTG-INFO-006", "Identify application entry points"],
        "NIST": [
            "AU-13", "Monitoring for Information Disclosure - Application Entry Points"
        ],
        "OWASP_TOP_10": ["A6", "Sensitive Data Exposure - Application Entry Points"],
    },
    "OWTF-IG-004": {
        "OWASP_V3": ["OWASP-IG-004", "Testing for Web Application Fingerprint"],
        "OWASP_V4": ["OTG-INFO-002", "Fingerprint Web Server"],
        "NIST": [
            "AU-13",
            "Monitoring for Information Disclosure - Application Fingerprinting",
        ],
        "OWASP_TOP_10": ["A6", "Sensitive Data Exposure - Application Fingerprinting"],
    },
    "OWTF-IG-005": {
        "OWASP_V3": ["OWASP-IG-005", "Application Discovery"],
        "OWASP_V4": ["OTG-INFO-004", "Enumerate Applications on Webserver"],
        "NIST": [
            "AU-13", "Monitoring for Information Disclosure - Application Discovery"
        ],
        "OWASP_TOP_10": [
            "A9", "Using Components with Known Vulnerabilities - Application Discovery"
        ],
    },
    "OWTF-IG-006": {
        "OWASP_V3": ["OWASP-IG-006", "Analysis of Error Codes"],
        "OWASP_V4": ["OTG-ERR-001", "Analysis of Error Codes"],
        "NIST": ["SI-11", "Error Handling"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Error Handling"],
        "CWE": ["CWE-209", "Information Exposure Through an Error Message"],
    },
    "OWTF-CM-001": {
        "category": "TLS",
        "OWASP_V3": ["OWASP-CM-001", "SSL/TLS Testing"],
        "OWASP_V4": ["OTG-INFO-011", "Map Network and Application Architecture"],
        "NIST": ["SC-13", "Cryptographic Protection - SSL/TLS implementation"],
        "OWASP_TOP_10": [
            "A9", "Using Components with Known Vulnerabilities - SSL/TLS implementation"
        ],
    },
    "OWTF-CM-002": {
        "OWASP_V3": ["OWASP-CM-002", "DB Listener Testing"],
        "OWASP_V4": ["OTG-CONFIG-002", "Test Application Platform Configuration"],
        "NIST": [
            "AC-03",
            "Access Enforcement - DB testing, Application Platform configuration",
        ],
        "OWASP_TOP_10": [
            "A5",
            "Security Misconfiguration - DB testing, Application Platform configuration",
        ],
        "CWE": [
            "CWE-16", "Configuration - DB testing, Application Platform configuration"
        ],
    },
    "OWTF-CM-003": {
        "OWASP_V3": ["OWASP-CM-003", "Infrastructure Configuration Management Testing"],
        "OWASP_V4": [
            "OTG-CONFIG-003", "Test File Extensions Handling for Sensitive Information"
        ],
        "NIST": ["CM-6", "Configuration Settings - File Extensions"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - File Extensions"],
        "CWE": ["CWE-16", "Configuration - File Extensions"],
    },
    "OWTF-CM-004": {
        "OWASP_V3": ["OWASP-CM-004", "Application Configuration Management Testing"],
        "OWASP_V4": [
            "OTG-CONFIG-004", "Backup and Unreferenced Files for Sensitive Information"
        ],
        "NIST": ["CM-6", "Configuration Settings - Backup and Unreferenced files"],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - Backup and Unreferenced files"
        ],
        "CWE": ["CWE-16", "Configuration - Backup and Unreferenced files"],
    },
    "OWTF-CM-005": {
        "OWASP_V3": ["OWASP-CM-005", "Testing for File Extensions Handling"],
        "OWASP_V4": [
            "OTG-CONFIG-005",
            "Enumerate Infrastructure and Application Admin Interfaces",
        ],
        "NIST": [
            "CM-10",
            "Software Usage Restrictions - File Extensions Handling, Admin interfaces",
        ],
        "OWASP_TOP_10": [
            "A5",
            "Security Misconfiguration - File Extensions Handling, Admin interfaces",
        ],
        "CWE": ["CWE-16", "Configuration - File Extensions Handling, Admin interfaces"],
    },
    "OWTF-CM-006": {
        "OWASP_V3": ["OWASP-CM-006", "Old backup and unreferenced files"],
        "OWASP_V4": ["OTG-CONFIG-006", "Test HTTP Methods"],
        "NIST": ["AC-03", "Access Enforcement - Old backup, unreferrenced files"],
        "OWASP_TOP_10": [
            "A6", "Sensitive Data Exposure - Old backup, unreferrenced files"
        ],
        "CWE": [
            "CWE-312",
            "Cleartext Storage of Sensitive Information - Old backup, unreferrenced files",
        ],
    },
    "OWTF-CM-007": {
        "OWASP_V3": ["OWASP-CM-007", "Infrastructure and Application Admin Interfaces"],
        "OWASP_V4": [
            "OTG-CONFIG-007", "Testing for Database credentials/connection strings"
        ],
        "NIST": [
            "AC-06",
            "Least Privilege - Admin interfaces, DB credentials/connection strings",
        ],
        "OWASP_TOP_10": [
            "A5",
            "Security Misconfiguration - Admin interfaces, DB credentials/connection strings",
        ],
        "CWE": [
            "CWE-16",
            "Configuration- Admin interfaces, DB credentials/connection strings",
        ],
    },
    "OWTF-CM-008": {
        "OWASP_V3": ["OWASP-CM-008", "Testing for HTTP Methods and XST"],
        "OWASP_V4": ["OTG-CONFIG-008", "Testing for Content Security Policy"],
        "NIST": ["CM-10", "Software Usage Restrictions - HTTP Methods, XST, CSP"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - HTTP Methods, XST, CSP"],
        "CWE": ["CWE-16", "Configuration - HTTP Methods, XST, CSP"],
    },
    "OWTF-AT-001": {
        "OWASP_V3": ["OWASP-AT-001", "Credentials transport over an encrypted channel"],
        "OWASP_V4": [
            "OTG-AUTHN-001",
            "Testing for Credentials Transported over an Encrypted Channel",
        ],
        "NIST": [
            "SC-13", "Cryptographic Protection - Encrypted transport of credentials"
        ],
        "OWASP_TOP_10": [
            "A9",
            "Using Components with Known Vulnerabilities - Encrypted transport of credentials",
        ],
    },
    "OWTF-AT-002": {
        "OWASP_V3": ["OWASP-AT-002", "Testing for user enumeration"],
        "OWASP_V4": [
            "OTG-IDENT-004",
            "Testing for Account Enumeration and Guessable User Account",
        ],
        "NIST": ["IA-6", "Authenticator Feedback - User enumeration"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - User enumeration"],
        "CWE": ["CWE-16", "Configuration - User enumeration"],
    },
    "OWTF-AT-003": {
        "OWASP_V3": ["OWASP-AT-003", "Testing for Guessable (Dictionary) User Account"],
        "OWASP_V4": ["OTG-AUTHN-002", "Testing for default credentials"],
        "NIST": ["IA-6", "Authenticator Feedback - Default and guessable credentials"],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - Default and guessable credentials"
        ],
        "CWE": ["CWE-16", "Configuration - Default and guessable credentials"],
    },
    "OWTF-AT-004": {
        "OWASP_V3": ["OWASP-AT-004", "Brute Force Testing"],
        "OWASP_V4": ["OTG-AUTHN-003", "Testing for Weak lock out mechanism"],
        "NIST": ["IA-6", "Authenticator Feedback - Brute force"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Brute force"],
        "CWE": ["CWE-16", "Configuration - Brute force"],
    },
    "OWTF-AT-005": {
        "OWASP_V3": ["OWASP-AT-005", "Testing for bypassing authentication schema"],
        "OWASP_V4": ["OTG-AUTHN-004", "Testing for bypassing authentication schema"],
        "NIST": ["AC-10", "Concurrent Session Control"],
        "OWASP_TOP_10": [
            "A2",
            "Broken Authentication and Session Management -bypassing authentication schema",
        ],
    },
    "OWTF-AT-006": {
        "OWASP_V3": [
            "OWASP-AT-006", "Testing for vulnerable remember password and pwd reset"
        ],
        "OWASP_V4": ["OTG-AUTHN-005", "Test remember password functionality"],
        "NIST": ["IA-6", "Authenticator Feedback - Remember Password functionality"],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - Remember Password functionality"
        ],
        "CWE": ["CWE-16", "Configuration - - Remember Password functionality"],
    },
    "OWTF-AT-007": {
        "OWASP_V3": ["OWASP-AT-007", "Testing for Logout and Browser Cache Management"],
        "OWASP_V4": ["OTG-AUTHN-006", "Testing for Browser cache weakness"],
        "NIST": ["AC-12", "Session Termination"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Session Termination"],
        "CWE": ["CWE-16", "Configuration - Session Termination"],
    },
    "OWTF-AT-008": {
        "OWASP_V3": ["OWASP-AT-008", "Testing for CAPTCHA"],
        "OWASP_V4": ["OTG-AUTHN-007", "Testing for Weak password policy"],
        "NIST": ["IA-3", "Device Identification and Authentication"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Device Identification"],
        "CWE": ["CWE-16", "Configuration - Device Identification"],
    },
    "OWTF-AT-009": {
        "OWASP_V3": ["OWASP-AT-009", "Testing Multiple Factors Authentication"],
        "OWASP_V4": ["OTG-IDENT-005", "Testing for Weak or unenforced username policy"],
        "NIST": [
            "IA-2",
            "Identification and Authentication (Organizational Users) - Multiple Factor Auth, weak/unenforced username policy",
        ],
        "OWASP_TOP_10": [
            "A2",
            "Broken Authentication and Session Management - Multiple Factor Auth, weak/unenforced username policy",
        ],
    },
    "OWTF-AT-010": {
        "OWASP_V3": ["OWASP-AT-010", "Testing for Race Conditions"],
        "OWASP_V4": [
            "OTG-AUTHZ-009",
            "Testing for failure to restrict access to authenticated resource",
        ],
        "NIST": [
            "SI-16",
            "Memory Protection - Race conditions, Bad authentication validation",
        ],
        "OWASP_TOP_10": [
            "A5",
            "Security Misconfiguration - Race conditions, Bad authentication validation",
        ],
        "CWE": [
            "CWE-16", "Configuration - Race conditions, Bad authentication validation"
        ],
    },
    "OWTF-SM-001": {
        "category": "Authentication",
        "OWASP_V3": ["OWASP-SM-001", "Testing for Session Management Schema"],
        "OWASP_V4": ["OTG-SESS-001", "Testing for Bypassing Session Management Schema"],
        "NIST": ["SC-10", "Network Disconnect"],
        "OWASP_TOP_10": [
            "A2",
            "Broken Authentication and Session Management - Session Management Schema",
        ],
    },
    "OWTF-SM-002": {
        "OWASP_V3": ["OWASP-SM-002", "Testing for Cookies attributes"],
        "OWASP_V4": ["OTG-SESS-002", "Testing for Cookies attributes"],
        "NIST": ["SC-23", "Session Authenticity - Cookie Attributes"],
        "OWASP_TOP_10": [
            "A2", "Broken Authentication and Session Management - Cookies attributes"
        ],
    },
    "OWTF-SM-003": {
        "OWASP_V3": ["OWASP-SM-003", "Testing for Session Fixation"],
        "OWASP_V4": ["OTG-SESS-003", "Testing for Session Fixation"],
        "NIST": ["SC-23", "Session Authenticity - Session Fixation"],
        "OWASP_TOP_10": [
            "A2", "Broken Authentication and Session Management - Session Fixation"
        ],
    },
    "OWTF-SM-004": {
        "OWASP_V3": ["OWASP-SM-004", "Testing for Exposed Session Variables"],
        "OWASP_V4": ["OTG-SESS-004", "Testing for Exposed Session Variables"],
        "NIST": ["AC-03", "Access Enforcement - Exposed session variables"],
        "OWASP_TOP_10": [
            "A2",
            "Broken Authentication and Session Management - Exposed Session Variables",
        ],
    },
    "OWTF-SM-005": {
        "category": "CSRF",
        "OWASP_V3": ["OWASP-SM-005", "Testing for CSRF"],
        "OWASP_V4": ["OTG-SESS-005", "Testing for Cross Site Request Forgery"],
        "NIST": ["SC-23", "Session Authenticity - CSRF"],
        "OWASP_TOP_10": ["A8", "Cross-Site Request Forgery"],
        "CWE": ["CWE-352", "Cross-Site Request Forgery"],
    },
    "OWTF-AZ-001": {
        "OWASP_V3": ["OWASP-AZ-001", "Testing Directory traversal/file include"],
        "OWASP_V4": ["OTG-AUTHZ-002", "Testing Directory traversal/file include"],
        "NIST": ["AC-6", "Least Privilege - Directory traversal"],
        "OWASP_TOP_10": ["A4", "Insecure Direct Object References"],
        "CWE": ["CWE-22", "Path Traversal"],
    },
    "OWTF-AZ-002": {
        "OWASP_V3": ["OWASP-AZ-002", "Testing for bypassing authorization schema"],
        "OWASP_V4": ["OTG-AUTHZ-003", "Testing for bypassing authorization schema"],
        "NIST": ["AC-6", "Least Privilege - Bypass authorization scheme"],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - Bypass authorization scheme"
        ],
        "CWE": ["CWE-16", "Configuration - Bypass authorization scheme"],
    },
    "OWTF-AZ-003": {
        "OWASP_V3": ["OWASP-AZ-003", "Testing for Privilege Escalation"],
        "OWASP_V4": ["OTG-AUTHZ-004", "Testing for Privilege Escalation"],
        "NIST": ["AU-9", "Protection of Audit Information"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Privilege Escalation"],
        "CWE": ["CWE-16", "Configuration - Privilege Escalation"],
    },
    "OWTF-DV-001": {
        "category": "XSS",
        "OWASP_V3": ["OWASP-DV-001", "Testing for Reflected Cross Site Scripting"],
        "OWASP_V4": ["OTG-INPVAL-001", "Testing for Reflected Cross Site Scripting"],
        "NIST": ["SI-10", "Information Input Validation - Reflected XSS"],
        "OWASP_TOP_10": ["A3", "Cross-Site Scripting(XSS) - Reflected XSS"],
        "CWE": ["CWE-79", "Cross-site Scripting - Reflected XSS"],
    },
    "OWTF-DV-002": {
        "category": "XSS",
        "OWASP_V3": ["OWASP-DV-002", "Testing for Stored Cross Site Scripting"],
        "OWASP_V4": ["OTG-INPVAL-002", "Testing for Stored Cross Site Scripting"],
        "NIST": ["SI-10", "Information Input Validation - Stored XSS"],
        "OWASP_TOP_10": ["A3", "Cross-Site Scripting(XSS) - Stored XSS"],
        "CWE": ["CWE-79", "Cross-site Scripting - Stored XSS"],
    },
    "OWTF-DV-003": {
        "category": "XSS",
        "OWASP_V3": ["OWASP-DV-003", "Testing for DOM based Cross Site Scripting"],
        "OWASP_V4": ["OTG-INPVAL-003", "Testing for HTTP Verb Tampering"],
        "NIST": [
            "SI-10", "Information Input Validation - DOM XSS, HTTP verb tampering"
        ],
        "OWASP_TOP_10": [
            "A3", "Cross-Site Scripting(XSS) - DOM XSS, HTTP verb tampering"
        ],
        "CWE": ["CWE-79", "Cross-site Scripting - DOM XSS, HTTP verb tampering"],
    },
    "OWTF-DV-004": {
        "OWASP_V3": ["OWASP-DV-004", "Testing for Cross Site Flashing"],
        "OWASP_V4": ["OTG-INPVAL-004", "Testing for HTTP Parameter pollution"],
        "NIST": ["SI-10", "Information Input Validation - XSS, HPP testing"],
        "OWASP_TOP_10": ["A3", "Cross-Site Scripting (XSS) - XSS, HPP testing"],
        "CWE": ["CWE-79", "Cross-site Scripting - XSS, HPP testing"],
    },
    "OWTF-DV-005": {
        "category": "SQL",
        "OWASP_V3": ["OWASP-DV-005", "SQL Injection"],
        "OWASP_V4": ["OTG-INPVAL-006", "Testing for SQL Injection"],
        "NIST": ["SI-10", "Information Input Validation - SQL injection"],
        "OWASP_TOP_10": ["A1", "Injection - SQL injection"],
        "CWE": ["CWE-89", "SQL Injection"],
    },
    "OWTF-DV-006": {
        "OWASP_V3": ["OWASP-DV-006", "LDAP Injection"],
        "OWASP_V4": ["OTG-INPVAL-007", "Testing for LDAP Injection"],
        "NIST": ["SI-10", "Information Input Validation - LDAP Injection"],
        "OWASP_TOP_10": ["A1", "Injection - LDAP Injection"],
        "CWE": ["CWE-90", "LDAP Injection"],
    },
    "OWTF-DV-007": {
        "OWASP_V3": ["OWASP-DV-007", "ORM Injection"],
        "OWASP_V4": ["OTG-INPVAL-008", "Testing for ORM Injection"],
        "NIST": ["SI-10", "Information Input Validation - ORM Injection"],
        "OWASP_TOP_10": ["A1", "Injection - ORM Injection"],
    },
    "OWTF-DV-008": {
        "OWASP_V3": ["OWASP-DV-008", "XML Injection"],
        "OWASP_V4": ["OTG-INPVAL-009", "Testing for XML Injection"],
        "NIST": ["SI-10", "Information Input Validation - XML Injection"],
        "OWASP_TOP_10": ["A1", "Injection - XML Injection"],
        "CWE": ["CWE-91", "XML Injection"],
    },
    "OWTF-DV-009": {
        "OWASP_V3": ["OWASP-DV-009", "SSI Injection"],
        "OWASP_V4": ["OTG-INPVAL-010", "Testing for SSI Injection"],
        "NIST": ["SI-10", "Information Input Validation - SSI Injection"],
        "OWASP_TOP_10": ["A1", "Injection - SSI Injection"],
    },
    "OWTF-DV-010": {
        "OWASP_V3": ["OWASP-DV-010", "XPath Injection"],
        "OWASP_V4": ["OTG-INPVAL-011", "Testing for XPath Injection"],
        "NIST": ["SI-10", "Information Input Validation - XPath Injection"],
        "OWASP_TOP_10": ["A1", "Injection - XPath Injection"],
        "CWE": ["CWE-91", "XPath Injection"],
    },
    "OWTF-DV-011": {
        "OWASP_V3": ["OWASP-DV-011", "IMAP/SMTP Injection"],
        "OWASP_V4": ["OTG-INPVAL-012", "IMAP/SMTP Injection"],
        "NIST": ["SI-10", "Information Input Validation - IMAP/SMTP Injection"],
        "OWASP_TOP_10": ["A1", "Injection - IMAP/SMTP Injection"],
    },
    "OWTF-DV-012": {
        "OWASP_V3": ["OWASP-DV-012", "Code Injection"],
        "OWASP_V4": ["OTG-INPVAL-013", "Testing for Code Injection"],
        "NIST": ["SI-10", "Information Input Validation - Code Injection"],
        "OWASP_TOP_10": ["A1", "Injection - Code Injection"],
        "CWE": ["CWE-77", "Command Injection"],
    },
    "OWTF-DV-013": {
        "OWASP_V3": ["OWASP-DV-013", "OS Commanding"],
        "OWASP_V4": ["OTG-INPVAL-014", "Testing for Command Injection"],
        "OWASP_TOP_10": ["A1", "Injection - Command Injection"],
        "CWE": ["CWE-78", "OS Injection"],
    },
    "OWTF-DV-014": {
        "OWASP_V3": ["OWASP-DV-014", "Buffer overflow"],
        "OWASP_V4": ["OTG-INPVAL-015", "Testing for Buffer overflow"],
        "NIST": ["SI-16", "Memory Protection - Buffer Overflow"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Buffer Overflow"],
        "CWE": ["CWE-16", "Configuration - Buffer Overflow"],
    },
    "OWTF-DV-015": {
        "OWASP_V3": ["OWASP-DV-015", "Incubated vulnerability"],
        "OWASP_V4": ["OTG-INPVAL-016", "Testing for incubated vulnerabilities"],
        "NIST": ["CM-10", "Software Usage Restrictions - incubated vulnerabilities"],
    },
    "OWTF-DV-016": {
        "OWASP_V3": ["OWASP-DV-016", "Testing for HTTP Splitting/Smuggling"],
        "OWASP_V4": ["OTG-INPVAL-017", "Testing for HTTP Splitting/Smuggling"],
        "NIST": ["SI-10", "Information Input Validation - HTTP Splitting/Smuggling"],
    },
    "OWTF-DS-001": {
        "category": "SQL",
        "OWASP_V3": ["OWASP-DS-001", "Testing for SQL Wildcard Attacks"],
        "NIST": ["SC-05", "Denial of Service Protection - SQL Wildcard Attacks"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - SQL Wildcard Attacks"],
        "CWE": ["CWE-16", "Configuration - SQL Wildcard Attacks"],
    },
    "OWTF-DS-002": {
        "OWASP_V3": ["OWASP-DS-002", "Locking Customer Accounts"],
        "NIST": ["SC-05", "Denial of Service Protection - Locking customer accounts"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Locking customer accounts"],
        "CWE": ["CWE-16", "Configuration - Locking customer accounts"],
    },
    "OWTF-DS-003": {
        "OWASP_V3": ["OWASP-DS-003", "Testing for DoS Buffer Overflows"],
        "NIST": ["SC-05", "Denial of Service Protection - DoS Buffer Overflows"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - DoS Buffer Overflows"],
        "CWE": ["CWE-16", "Configuration - DoS Buffer Overflows"],
    },
    "OWTF-DS-004": {
        "OWASP_V3": ["OWASP-DS-004", "User Specified Object Allocation"],
        "NIST": ["SC-05", "Denial of Service Protection - Object Allocation"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - DoS Object Allocation"],
        "CWE": ["CWE-16", "Configuration - DoS Object Allocation"],
    },
    "OWTF-DS-005": {
        "OWASP_V3": ["OWASP-DS-005", "User Input as a Loop Counter"],
        "NIST": ["SC-05", "Denial of Service Protection - User input as loop counter"],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - DoS user input as loop counter"
        ],
        "CWE": ["CWE-16", "Configuration - DoS user input as loop counter"],
    },
    "OWTF-DS-006": {
        "OWASP_V3": ["OWASP-DS-006", "Writing User Provided Data to Disk"],
        "NIST": ["SC-05", "Denial of Service Protection - Writing input data to disk"],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - DoS Writing input data to disk"
        ],
        "CWE": ["CWE-16", "Configuration - DoS Writing input data to disk"],
    },
    "OWTF-DS-007": {
        "OWASP_V3": ["OWASP-DS-007", "Failure to Release Resources"],
        "NIST": [
            "SC-05", "Denial of Service Protection - Failure to release resources"
        ],
        "OWASP_TOP_10": [
            "A5", "Security Misconfiguration - DoS Failure to release resources"
        ],
        "CWE": ["CWE-16", "Configuration - DoS Failure to release resources"],
    },
    "OWTF-DS-008": {
        "OWASP_V3": ["OWASP-DS-008", "Storing too Much Data in Session"],
        "NIST": ["SC-05", "Denial of Service Protection - Large session data"],
        "OWASP_TOP_10": ["A5", "Security Misconfiguration - Large session data"],
        "CWE": ["CWE-16", "Configuration - Large session data"],
    },
    "OWTF-WS-001": {
        "OWASP_V3": ["OWASP-WS-001", "WS Information Gathering"],
        "NIST": [
            "AU-13", "Monitoring for Information Disclosure - Information Gathering"
        ],
    },
    "OWTF-WS-002": {
        "OWASP_V3": ["OWASP-WS-002", "Testing WSDL"],
        "NIST": ["AU-13", "Monitoring for Information Disclosure - WSDL testing"],
    },
    "OWTF-WS-003": {"OWASP_V3": ["OWASP-WS-003", "XML Structural Testing"]},
    "OWTF-WS-004": {"OWASP_V3": ["OWASP-WS-004", "XML content-level Testing"]},
    "OWTF-WS-005": {
        "OWASP_V3": ["OWASP-WS-005", "HTTP GET parameters/REST Testing"],
        "NIST": [
            "SI-10", "Information Input Validation - HTTP parameters/REST testing"
        ],
    },
    "OWTF-WS-006": {
        "OWASP_V3": ["OWASP-WS-006", "Naughty SOAP attachments"],
        "NIST": ["CM-10", "Software Usage Restrictions - Naughty SOAP attachments"],
    },
    "OWTF-WS-007": {
        "OWASP_V3": ["OWASP-WS-007", "Replay Testing"],
        "NIST": [
            "IA-2",
            "Identification and Authentication (Organizational Users) - Replay testing",
        ],
    },
    "OWTF-AJ-001": {
        "OWASP_V3": ["OWASP-AJ-001", "AJAX Vulnerabilities"],
        "NIST": ["AC-03", "Access Enforcement - AJAX vulnerabilities"],
    },
    "OWTF-AJ-002": {
        "OWASP_V3": ["OWASP-AJ-002", "AJAX Testing"],
        "NIST": ["AC-03", "Access Enforcement - AJAX testing"],
    },
}
