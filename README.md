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

- Durable sessions and normalized URL targets.
- OWTF plugin manifests with established short technique codes.
- OWTF plugin groups and types, including group launches and ``quiet`` mode.
- Named OWTF profiles with deterministic plugin ordering recorded on each run.
- A built-in HTTP collector, trusted host-command plugins, and isolated
  container plugins with forced cleanup.
- Requirement discovery with visible ready, unavailable, and blocked states.
- A bounded worklist with cancellation of the plugin process group.
- Worker state, task events, HTTP transactions, artifacts, observations, and
  findings stored in SQLite.
- HAR transaction import with retained source, request, and response files.
- An OWTF-owned HTTP/HTTPS interception proxy with a persistent CA, bounded HAR
  capture and cache, retries, WebSocket tunneling and frame transcripts, host
  scope, and outbound HTTP/HTTPS/SOCKS5 proxy support.
- A loopback proxy API and CLI for transaction history, filtering,
  statistics, clearing, CA download, and binary-safe request replay.
- Challenge-based Basic and Digest authentication for explicitly configured
  target hosts.
- Priority-ordered static request and response interceptors with bounded URL,
  header, body, and delay actions.
- Strict, versioned configuration shared by the server and proxy, with
  scriptable show and validation commands.
- Target reports through the API and CLI.
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

Set `OWTF_URL` when the server is not at its default address. Runtime state is
stored under `.owtf/` unless configuration, `OWTF_DATA_DIR`, or `--data-dir`
changes it.

## Run with Docker

Docker is optional. Compose starts one resource-bounded OWTF service backed by
a named SQLite data volume:

```bash
make local-up
make local-status
make local-logs
make local-down
```

The default is one worker. Set `OWTF_WORKERS` deliberately if the host has
capacity for more.

## Verify changes

```bash
make lint
make test-unit
make test-api
```

The smoke test starts an isolated one-worker server in a temporary directory,
exercises the API with curl, exercises the CLI against that same server, and
removes its state afterward. It does not start Docker.

## Access control

OWTF has no user or authentication subsystem. Bind it to localhost for
single-operator use. Put shared or remote deployments behind an
identity-aware reverse proxy such as
[oauth2-proxy](https://github.com/oauth2-proxy/oauth2-proxy).

Use OWTF only on systems you own or are explicitly authorized to test.

## License

OWTF is distributed under the [BSD 3-Clause license](LICENSE.md).
