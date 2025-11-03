# OWASP Offensive Web Testing Framework (OWTF) Security Policy

The OWTF leadership team takes security issues seriously. We value coordinated disclosure and will work with you to understand
and remediate vulnerabilities in a timely manner.

We aim to acknowledge new reports within **3 business days** and, where a fix is accepted, release an update within **7 business
days**. If a report is declined we will explain why.

## Reporting a vulnerability

Email the project maintainers at [owasp_owtf_developers@lists.owasp.org](mailto:owasp_owtf_developers@lists.owasp.org) with the
following details:

1. Your name and affiliation (if any)
2. A clear description of the vulnerability
3. Steps to reproduce the issue, including sample payloads or proof-of-concept code if applicable
4. Any related CVE, advisory, or public references
5. Your expectation for disclosure timelines (if different from the defaults above)

Please encrypt sensitive information if possible. If you need a PGP key, request one in your initial email and we will provide it.

## Scope

The security policy applies to:

- The OWTF core framework and official plugins hosted in this repository
- Infrastructure maintained by the OWTF project that directly supports users (for example, official Docker images)

Third-party tools invoked by OWTF plugins fall outside of our direct control. We will coordinate with upstream projects when
feasible but cannot guarantee fixes for external dependencies.

## Supported versions

We support the latest tagged release and the `develop` branch. Security fixes are generally backported to the most recent stable
release.

## Acknowledgements

We maintain a [hall of fame](https://github.com/OWASP/OWTF/blob/master/hall_of-fame.md) to recognise individuals and
organisations that responsibly disclose security issues.
