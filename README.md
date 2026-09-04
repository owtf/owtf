# Offensive Web Testing Framework (OWTF)

[![Build status](https://github.com/owtf/owtf/actions/workflows/main.yml/badge.svg)](https://github.com/owtf/owtf/actions/workflows/main.yml)
[![License: BSD 3-Clause](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg?style=flat-square)](LICENSE.md)
[![Go](https://img.shields.io/badge/Go-1.24-00ADD8.svg)](https://go.dev/)

OWTF is a penetration tester's harness for authorized security research,
plugin execution, evidence capture, and vulnerability reporting. It keeps
the established OWTF concepts of sessions, targets, plugin codes, worklist,
workers, transactions, and reports while replacing the retired Python runtime
with a small Go and SQLite core.

OWTF is not a scanner and is not a substitute for operator judgment. Plugins
run techniques or external tools; OWTF coordinates them and preserves the
resulting evidence.

## Current capabilities

- Durable session lifecycle and normalized URL, host, IP, and CIDR targets.
- Persisted target scope plus bounded target search and pagination.
- OWTF plugin manifests with established short technique codes.
- Structured OWTF technique titles, hints, priorities, and references retained
  in the plugin catalog, task history, and reports.
- Typed, bounded plugin inputs with defaults recorded on every task.
- Named, bounded wordlists copied into task-owned storage before execution.
- OWTF plugin groups and types, including group launches and ``quiet`` mode.
- Declarative external plugins that retain curated manual-testing guidance
  without contacting the target.
- Declarative grep plugins that match bounded captured headers and bodies while
  retaining transaction provenance.
- Named OWTF profiles with deterministic plugin ordering recorded on each run.
- A built-in HTTP collector, trusted host-command plugins, and isolated
  container plugins with forced cleanup.
- Requirement discovery with visible ready, unavailable, and blocked states.
- A bounded worklist with process-group cancellation and per-attempt history.
- Worker state, task events, HTTP transactions, artifacts, observations, and
  findings stored in SQLite.
- Execution metrics for task states, completed-attempt durations, retained
  evidence, and the live worker pool.
- HAR transaction import with retained source, request, and response files.
- Per-target URL catalogs for plugin discoveries and retained traffic, with
  canonical deduplication, visited and scope classification, bounded search,
  and report inclusion.
- Bounded search and pagination over persisted transaction metadata.
- An OWTF-owned HTTP/HTTPS interception proxy with a persistent CA, bounded HAR
  capture and cache, retries, WebSocket tunneling and frame transcripts, host
  scope, and outbound HTTP/HTTPS/SOCKS5 proxy support.
- A loopback proxy API and CLI for transaction history, filtering,
  statistics, clearing, CA download, and binary-safe request replay.
- Challenge-based Basic and Digest authentication for explicitly configured
  target hosts.
- Priority-ordered request and response interceptors with bounded URL, header,
  body, and delay actions, plus atomic runtime management through the loopback
  API and CLI.
- Bounded live request and response interception with inspect, edit, continue,
  drop, timeout, and shutdown release through the loopback API and CLI.
- Strict, versioned configuration shared by the server and proxy, with
  scriptable show and validation commands.
- Target and session reports with evidence-preserving output dispositions,
  ranks, notes, and append-only review history through the API and CLI.
- One API used by the CLI and the embedded proof UI.
- No accounts, passwords, tokens, or user database.

See [the architecture](docs/architecture/overview.rst), [CLI
reference](docs/usage/cli.rst), and [legacy technique
inventory](docs/architecture/legacy-plugin-inventory.csv). The checked
[feature-parity matrix](docs/architecture/feature-parity.csv) tracks what is
implemented, partial, missing, intentionally replaced, removed, or deferred.

## Run locally

Install Go 1.24 or newer, then build and start OWTF:

```bash
make build
./build/owtf serve
```

OWTF checks `.owtf/config.yaml` when present. Inspect the effective redacted
settings or validate a file before startup:

```bash
./build/owtf config show
./build/owtf config validate .owtf/config.yaml
```

The API and embedded proof UI are available at `http://127.0.0.1:8009`.
The CLI uses the same API:

```bash
./build/owtf health
./build/owtf sessions list
./build/owtf scan --plugin OWTF-WSP-001-active https://example.com
./build/owtf worklist
./build/owtf proxy --target-host example.com
```

Startup and interactive plugin listings use the familiar OWTF banner and terminal
formatting. Other command responses currently remain JSON. Pass `--json` for
machine output or `--human` to request presentation where it is implemented.

Run `make demo-cli` for a verified Compose instance with sample results and a
CLI wrapper you can try. `make test-compose` checks the same lifecycle and cleans
up afterward. See [backup, restore, and the CLI walkthrough](docs/usage/recovery.rst).

Set `OWTF_URL` when the server is not at its default address. Runtime state is
stored under `.owtf/` unless configuration, `OWTF_DATA_DIR`, or `--data-dir`
changes it.

## Run with Docker

Docker is optional. Compose starts one resource-bounded OWTF service backed by
a named SQLite data volume:

```bash
make install       # Build OWTF and owtf/kali-tools:local
make local-up
make local-status
make local-logs
make local-down
```

The default is one worker. Set `OWTF_WORKERS` deliberately if the host has
capacity for more.

`make install` prepares both images without starting services. Docker reuses
cached layers on subsequent installs. The Kali image contains the external
scanners and can take substantial disk space. For the service alone, use
`make local-up`; for just the tools image, use `make tools-image`.

### External scanner tools

The retained Testssl.sh, WAFW00F, Gobuster, Metagoofil, WhatWeb, Nuclei,
Wapiti, Nmap, and Nikto plugins use a separate Kali image, built by `make install`.
To build only that image:

```bash
make tools-image
./build/owtf serve
```

The server needs a working Docker CLI and context. OWTF never pulls images
implicitly. The Compose server deliberately has no Docker socket or CLI;
use the host server for this container-plugin workflow. Scanner containers
receive bounded inputs and task-owned volumes, not host-directory mounts.
Reports are exported before all task containers and volumes are removed.

### DNS name discovery

`PTES-011-bruteforce` uses Gobuster against an explicit DNS resolver. Put a
reviewed wordlist in the configured `plugins.wordlistDirectory` (`wordlists/`
by default): one label such as `www` or `api` per line, not URLs or full names.
The limit is 1,000 labels and 64 KiB. For an authorized target, for example:

```bash
./build/owtf scan --plugin PTES-011-bruteforce \
  --input PTES-011-bruteforce.wordlist=names.txt \
  --input PTES-011-bruteforce.resolver=192.0.2.53:53 \
  example.test
```

Replace the example resolver with your DNS server. Results retain A/AAAA
addresses as `dns.name` observations and the original `dns.txt`. They appear
in target/session reports without inventing HTTP URLs or creating new targets.
Use the existing target-add command to select discoveries for further work.
Wildcard DNS aborts the task with its diagnostic in the logs; it does not
create findings for every dictionary entry. An empty result is not proof that
no names exist: the wordlist and selected resolver bound the check.
Resolver errors fail the task even when Gobuster exits zero; raw partial
output remains available but is not promoted to successful discoveries.

`PTES-009-active.port` now applies to both the Nmap port scan and SMB scripts,
including non-default ports such as 1445.

## Verify changes

```bash
make lint
make test-unit
make test-api
```

The smoke test starts an isolated one-worker server in a temporary directory,
exercises the API with curl, exercises the CLI against that same server, and
removes its state afterward. It does not start Docker: container plugins must
remain blocked, without attempts or fabricated scanner artifacts.

With the Kali image already built, run `make test-tools` for real scanner
execution against temporary local HTTP/TLS, FTP, SMTP, SMB, and DNS fixtures. It checks
Postfix capabilities, Samba SMB2/SMB3 dialects and required/optional signing,
Nmap service and NSE observations, closed-port handling, unranked Nikto findings,
affected URLs, Gobuster virtual hosts, and DNS A/AAAA discoveries. DNS tests
include NXDOMAIN, wildcard refusal, and rejection of invalid wordlists before
container execution. The custom SMB-port check closes 445 to rule out fallback.
API, CLI, and offline
JSON/HTML reports must contain the decoded results; exported raw XML must match
the API artifact bytes. The gate also checks metrics, cancellation,
and container/volume cleanup without rebuilding the tools image. SMTP and SMB
stay on the Docker bridge, without published host ports. The SMTP fixture
rejects mail delivery. Captured XML regression fixtures also run in normal CI.
Windows NTLM and SMB1 remain outside this live coverage.
Metagoofil receives a startup check only; its search-provider
workflow requires a separate authorized live test.

Run `make test-failures` to check only cancellation, scanner process death,
and OWTF's task deadline using the existing Kali image. Every case waits for
both a target-side request and Gobuster output before fault injection, then
checks status, attempt-linked logs, container/volume cleanup, and absence of
retries after server restart. Native process tests also check a stubborn
parent/child/grandchild tree, including parent death with inherited output pipes.
API/CLI results and Docker snapshots are retained under `build/test-evidence/`;
`make clean` removes them. The full `make test-tools` run includes these checks.

## Access control

OWTF has no user or authentication subsystem. Bind it to localhost for
single-operator use. Put shared or remote deployments behind an
identity-aware reverse proxy such as
[oauth2-proxy](https://github.com/oauth2-proxy/oauth2-proxy).

Use OWTF only on systems you own or are explicitly authorized to test.

## License

OWTF is distributed under the [BSD 3-Clause license](LICENSE.md).
