# OWASP Offensive Web Testing Framework (OWTF) Security Policy

The OWTF leadership team takes security issues seriously. We value coordinated disclosure and will work with reporters to
understand, remediate, and disclose vulnerabilities responsibly. Response and remediation times depend on maintainer
availability, severity, and the complexity of the fix; we will agree on a disclosure timeline after triage.

## Reporting a vulnerability

Do **not** open a public issue or discussion containing vulnerability details.

Email the current [OWTF project leaders](https://owasp.org/www-project-owtf/#div-leaders) at
[viyat.bhalodia@owasp.org](mailto:viyat.bhalodia@owasp.org) and
[abraham.aranguren@owasp.org](mailto:abraham.aranguren@owasp.org) with the subject `[OWTF SECURITY]`. Include:

1. Your name and affiliation (if any)
2. A clear description of the vulnerability
3. Steps to reproduce the issue, including sample payloads or proof-of-concept code if applicable
4. Any related CVE, advisory, or public references
5. Your preferred disclosure timeline

If you need an encrypted channel, send an initial message without sensitive technical details and ask the maintainers to arrange
one.

## Scope

The security policy applies to:

- The OWTF core framework and official plugins hosted in this repository
- Infrastructure maintained by the OWTF project that directly supports users (for example, official Docker images)

Third-party tools invoked by OWTF plugins fall outside of our direct control. We will coordinate with upstream projects when
feasible but cannot guarantee fixes for external dependencies.

## Supported versions

| Version                           | Supported |
| --------------------------------- | --------- |
| `develop`                         | Yes       |
| `2.6.0` and older tagged releases | No        |

The `develop` branch is pre-release software and is currently the only line receiving security fixes. Tagged releases do not
currently receive security backports. This table will be updated when a new stable release is published.

## Acknowledgements

With the reporter's consent, we credit responsible disclosures in the corresponding published GitHub security advisory.
