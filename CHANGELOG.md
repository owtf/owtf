# Changelog

Notable user-facing changes to OWTF are recorded here. Release entries are curated from merged pull requests and use
[GitHub Releases](https://github.com/owtf/owtf/releases) as the canonical source for downloadable versions.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [2.7.0] - 2026-09-02

### Added

- Added a complete intercepting-proxy workspace with HTTPS interception, transaction history, live interception, and a request repeater.
- Added a reviewed community-plugin marketplace with upload validation, administrator approval, owner visibility, and execution through the normal OWTF work queue.
- Added priority-based scheduling, dynamic worker scaling, execution timeouts and retries, output fingerprinting, and execution metrics with HTML reporting.
- Added Azure, Terraform, and Kubernetes deployment resources.
- Added and refreshed discovery plugins for cloud storage, LDAP, IMAP/SMTP injection, Gobuster, BBOT, AJAX behavior, and TLS testing.

### Changed

- Raised the supported runtime to Python 3.11 and 3.12, removed remaining Python 2 runtime paths, and migrated packaging to `pyproject.toml`.
- Modernized the React application and continued its TypeScript migration, including the proxy and community-plugin interfaces.
- Split the development containers into frontend, backend, and PostgreSQL services and standardized the supported startup path on Docker Compose.
- Replaced the Sphinx documentation with a responsive, searchable MkDocs Material site.
- Consolidated the supported end-user installation instructions around Docker Compose.
- Replaced the legacy issue template with dedicated bug, feature, and documentation forms.
- Consolidated contributor guidance in the repository-root `CONTRIBUTING.md`.
- Updated public project, documentation, support, and community links.

### Fixed

- Fixed the supported Docker Compose quick start so the backend installs OWTF's package metadata and console entry points correctly.
- Added first-run proxy certificate generation with persistent Compose storage, and exposed the proxy on loopback-only host ports.
- Fixed targets disappearing from the active session and corrected selected-plugin execution.
- Fixed proxy interceptor response handling, cache lock timeouts, and process termination escalation.
- Fixed work-queue claiming and draining gaps, timeout and exception outcomes, and duplicate plugin output under concurrent execution.

### Security

- Added authenticated OWTF accounts and tightened access to targets, reports, proxy traffic, and community-plugin administration.
- Hardened community-plugin validation against aliased imports and shell-execution bypasses, and made persisted administrator state authoritative.
- Removed obsolete frontend build plugins, resolved all critical advisories reported by Yarn, and added a CI gate that blocks new critical frontend dependency advisories.
- Clarified the private vulnerability-reporting process and the versions that currently receive security fixes.

## [2.6.0] - 2022-03-16

The original release did not include detailed release notes. See the
[changes since 2.5.0](https://github.com/owtf/owtf/compare/v2.5.0...v2.6.0) and the
[v2.6.0 release](https://github.com/owtf/owtf/releases/tag/v2.6.0).

## Earlier releases

- [2.5.0](https://github.com/owtf/owtf/releases/tag/v2.5.0) - 2019-03-28
- [2.4](https://github.com/owtf/owtf/releases/tag/v2.4) - 2018-05-16
- [2.3](https://github.com/owtf/owtf/releases/tag/v2.3) - 2018-04-02
- [2.3b "MacinOWTF"](https://github.com/owtf/owtf/releases/tag/v2.3b) - 2017-10-25
- [2.2b "Rolling Reboot"](https://github.com/owtf/owtf/releases/tag/v2.2b) - 2017-10-25
- [2.1a "Chicken Korma"](https://github.com/owtf/owtf/releases/tag/v2.1a) - 2017-04-25
- [2.0a "Tikka Masala"](https://github.com/owtf/owtf/releases/tag/v2.0a) - 2016-05-14
- [All historical releases](https://github.com/owtf/owtf/releases)
- [Legacy detailed changelog](https://github.com/owtf/owtf/blob/v2.6.0/CHANGELOG.md)

[unreleased]: https://github.com/owtf/owtf/compare/v2.7.0...develop
[2.7.0]: https://github.com/owtf/owtf/compare/v2.6.0...v2.7.0
