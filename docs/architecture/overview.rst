OWTF
=========

Purpose
-------

OWTF is a local-first harness for authorized security testing. An
operator defines targets, runs repeatable techniques, inspects live work and
logs, preserves HTTP transactions and artifacts, and produces evidence-backed
reports. AI may help organize and explain evidence, but it does not silently
expand scope or invent findings.

Product decisions
-----------------

* One Go binary with bounded local workers.
* SQLite for durable state and content-addressed files for artifacts.
* No OWTF users, passwords, tokens, or authorization database. Deployments that
  need access control must put OWTF behind an authenticating reverse proxy such
  as oauth2-proxy. An OWTF session is only a named scan workspace; it is not an
  authenticated user session.
* Docker Compose is the supported packaged runtime. SQLite removes the database
  service; local Go execution remains available for development and tests.
* Plugins remain a central product concept and retain OWTF technique codes.
* The replacement is outcome-compatible, not implementation-compatible. There
  is no shim around the legacy Python runtime.

Plugin layout
-------------

Plugin source is organized by stable OWTF technique code and plugin type::

  plugins/
    OWTF-IG-004/
      semi_passive/
        plugin.yaml
    OWTF-WSP-001/
      active/
        plugin.yaml

The manifest ID includes both parts, such as
``OWTF-IG-004-semi_passive``. Each manifest also declares its established OWTF
plugin group (``web``, ``network``, or ``auxiliary``). The directory is for
maintainers; the manifest remains the runtime source of truth and the catalog
discovers it recursively.

Core model
----------

``Session``
  Named body of work containing targets, runs, evidence, and reports.

``Target``
  A normalized URL, hostname, IP address, or CIDR. Duplicate values within an
  session are rejected.

``Plugin``
  A versioned manifest for one executable technique. IDs use the existing code
  plus its plugin type, for example ``OWTF-WSP-001-active``.

``Run`` and ``Task``
  A run is an immutable launch plan. Each target/plugin pair becomes a durable
  task with attempts, timestamps, terminal status, and an explicit error.

``Event``
  Ordered lifecycle, stdout, and stderr output attached to a task attempt.

``Transaction`` and ``Artifact``
  Captured request/response metadata and immutable raw evidence. Transactions
  belong to targets; a task reference is present only when a plugin produced
  the transaction. Artifacts are addressed by SHA-256 rather than by mutable
  report paths.

``Observation`` and ``Finding``
  An observation is a tool fact. A finding is a reviewable security conclusion.
  Keeping them separate prevents scanner output from becoming a report claim
  without provenance.

Required behavior
-----------------

The replacement is not ready to supersede the old application until it can:

1. Create a session and add, normalize, deduplicate, list, and delete target
   URLs, hosts, IP addresses, and CIDRs.
2. Discover available plugins and explain unavailable requirements.
3. Launch one plugin, a selected set, or an OWTF plugin group against selected
   targets.
4. Show a truthful worklist derived from persisted task state and a fixed,
   configured worker count.
5. Show ordered lifecycle, stdout, and stderr events for every attempt.
6. Capture and browse HTTP transactions and retained artifacts.
7. Render target and session reports with technique, task, and evidence
   provenance, then export them without requiring the server.
8. Cancel work, recover interrupted work after restart, and leave no task in an
   ambiguous state.

Plugin execution
----------------

The manifest is declarative. It identifies the plugin, version, OWTF technique
codes, group, type, runtime, requirements, and supported target kinds.

The first runtime is a Go builtin used to prove the contract. A local command
runtime expresses trusted executables as argument arrays. Target and
configuration values are passed as individual arguments or environment values;
they are never interpolated into shell source. This prevents OWTF from turning
target text into shell syntax, but it does not sandbox the executable. Host
command plugins are trusted code with the same operating-system access as OWTF.

Container plugins are the isolation boundary for third-party tools. They use a
read-only filesystem, dropped capabilities, no-new-privileges, bounded memory,
CPU, and process counts, and forced removal after success, failure, timeout, or
cancellation. Network access remains disabled until the per-task OWTF capture
proxy is the container's only egress path.

Missing required executables make a plugin unavailable before a run starts. An
unavailable plugin selected directly fails before a run is created. During a
plugin-group launch, unavailable or incompatible plugins remain visible as
blocked worklist entries with the exact reason. Plugins do not open SQLite or
call internal Go packages.

Delivery phases and gates
-------------------------

Phase 1: durable vertical slice
  Session and target lifecycle, plugin catalog, one bounded runner, one real
  HTTP collector, events, transactions, artifacts, target report, and restart
  recovery. The gate is an end-to-end API test plus a browser screenshot of a
  real report after process restart.

Phase 2: command plugins
  Requirement checks, safe argument construction, cancellation, process-group
  cleanup, limits, and a small maintained baseline of OWTF techniques. The gate
  uses real tool fixtures and verifies missing-tool and cancellation paths.

Phase 3: CLI and reporting
  Make every operator workflow available through the Go CLI: sessions, target
  intake, individual and plugin-group launches, worklist, workers, logs,
  cancellation,
  transactions, evidence, reports, and portable exports. The CLI calls the same
  HTTP API and emits scriptable JSON. The gate is a complete CLI-driven scan and
  an offline report opened without the server.

Phase 4: capture proxy
  Implement the historical OWTF proxy outcomes in a smaller Go package: HTTP
  methods, CONNECT/TLS interception, transaction capture, bounded response
  caching and cookie filtering, retries, WebSocket tunneling, outbound
  HTTP/HTTPS/SOCKS5 proxies, upstream authentication, repeater, CA download,
  and request/response interceptors. Captures use the same HAR boundary as
  imports; broken object lifecycles from the retired Tornado implementation are
  not preserved.

Phase 5: captured plugin execution
  Give each container task a private network and a task-owned OWTF proxy as its
  only egress path. Import its HAR into the task and target before completion,
  and destroy the plugin container, proxy, and network together on every exit
  path.

Phase 6: AI assistance
  Add optional evidence search and AI summaries that cite stored observations
  and artifacts. Human-reviewed findings remain authoritative.

Phase 7: operator UI
  Build the final React and TypeScript interface with Tailwind and shadcn
  primitives, compact Inter typography, and complete parity with the CLI. Every
  screen uses the real API; no demo counters or simulated progress. The current
  embedded interface is disposable proof tooling, not the product UI.

Phase 8: legacy retirement
  Publish a mapping from retained OWTF technique codes to replacement plugins.
  Deprecate a legacy feature only after its replacement passes a documented
  outcome test. Unsupported and unreliable plugins remain available in the old
  release; they are not copied into the new runtime by default.

Implemented gates
-----------------

Phase 1 was exercised end to end with a real HTTP target, persisted SQLite
state, process restart, target report, transaction, observation, task events,
and downloadable content-addressed evidence.

Phase 2 was exercised with the real ``curl`` command plugin
``OWTF-IG-004-semi_passive``. Automated tests also verify missing-command
visibility, non-shell argument handling, task cancellation, and termination of
the complete plugin process group, including a child that ignores the initial
termination signal.

Phase 3 was exercised through the Go CLI against a live one-worker server. The
gate covers sessions, targets, individual and grouped plugin launches, worklist,
workers, ordered logs, cancellation, transactions, reports, artifact downloads,
and portable ZIP export.

Phase 4 is in progress. The import boundary accepts standard HAR files through
both curl and the Go CLI, retains source, request, and response bodies, and
creates no fake plugin work. The OWTF proxy handles HTTP and CONNECT/TLS,
persists its CA, records bounded HAR captures, tunnels WebSockets, enforces an
optional host scope, retries failures and HTTP 408/599 responses, caches bounded
responses with cookie-key filtering, and supports authenticated HTTP, HTTPS,
and SOCKS5 upstream proxies. Origin HTTP authentication, WebSocket frame
artifacts, repeater, CA and history APIs, and static/live interceptors remain
before the phase gate.

API regression gate
-------------------

Run ``make test-api`` to start an isolated one-worker server and exercise
the complete implemented HTTP surface with ``curl``. The same run invokes every
CLI command category against the live server while curl independently verifies
the resulting state. The test uses temporary plugins for deterministic
cancellation and a missing requirement, removes its database and artifacts on
exit, and does not start Docker or Colima. Run ``make clean`` after
development to remove the bounded Go build cache under ``/tmp``.

Resource discipline
-------------------

Native tests run before containers, with bounded test and worker concurrency.
Go caches and proof data may live outside the worktree. Compose builds only the
single OWTF service and mounts one data volume. Each phase records binary,
image, database, and artifact sizes so growth is visible rather than accidental.
