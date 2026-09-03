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

Named ordering profiles are separate versioned files::

  profiles/
    default.yaml

A profile orders a group launch but never acts as a hidden allowlist. Matching
plugins omitted from the profile still run afterward in stable ID order.

Core model
----------

``Session``
  Named body of work containing targets, runs, evidence, and reports.

``Target``
  A normalized URL, hostname, IP address, or CIDR. Duplicate values within an
  session are rejected. Scope is mutable review state; target identity is not.

``Plugin``
  A versioned manifest for one executable technique. IDs use the existing code
  plus its plugin type, for example ``OWTF-WSP-001-active``.

``Technique``
  The established OWTF test-group code, title, hint, priority, and reference.
  Plugin type variants share identical metadata for the same code. A task keeps
  the metadata from its immutable plugin snapshot.

``Run`` and ``Task``
  A run is an immutable launch plan. Each target/plugin pair becomes a durable
  task with attempts, timestamps, terminal status, and an explicit error. A
  group run also records the OWTF profile that fixed its plugin order.

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
9. Account for every legacy plugin variant with a runnable maintained plugin or
   an explicit unsupported reason, while preserving its OWTF code, group, and
   type.

Plugin execution
----------------

The manifest is declarative. It identifies the plugin, version, OWTF technique
metadata, group, type, runtime, requirements, supported target kinds, and
optional operator inputs. Inputs use the small ``string``, ``integer``, and ``boolean``
type set. String choices and integer bounds describe validation and provide the
same rendering contract to the CLI, API, and final UI.

An ``external`` plugin contains bounded guidance and validated HTTP/S
references. It records that material as a target observation without starting
a process or sending traffic. This replaces the legacy Python wrappers around
resource lists while retaining the ``external`` plugin type and short code.

A ``grep`` plugin applies declarative RE2 rules to captured transaction URLs,
headers, and bodies. The runner supplies a read-only transaction reader rather
than a database handle. It loads only requested bodies, refuses more than
10,000 transactions or an individual body over 8 MiB, and records matched
transaction IDs instead of copying evidence into plugin output.

Launch input is non-secret because its resolved value is intentionally retained
on every task and included in reports. Defaults are resolved once when the task
is created. Unknown, missing, incorrectly typed, and out-of-bounds values fail
before work is queued. A queued task also retains the complete plugin manifest;
if that manifest changes before execution, OWTF rejects the task rather than
silently running a different command.

The first runtime is a Go builtin used to prove the contract. A local command
runtime expresses trusted executables as argument arrays. Target, artifact, and
input placeholders must occupy a complete argument. They are never interpolated
into shell source. This prevents OWTF from turning target or operator text into
shell syntax, but it does not sandbox the executable. Host command plugins are
trusted code with the same operating-system access as OWTF.

Container plugins are the isolation boundary for third-party tools. They use a
read-only filesystem, dropped capabilities, no-new-privileges, bounded memory,
CPU, and process counts, and forced removal after success, failure, timeout, or
cancellation. Container network access remains disabled by default. Networked
container execution is deferred and is not part of the current delivery plan.

Missing required executables make a plugin unavailable before a run starts. An
unavailable plugin selected directly fails before a run is created. During a
plugin-group launch, unavailable or incompatible plugins remain visible as
blocked worklist entries with the exact reason. Plugins do not open SQLite or
call internal Go packages.

Configuration
-------------

The legacy ``settings.py`` module is not a parity target. It mixed process
startup, database credentials, authentication, UI ports, proxy behavior, tool
paths, plugin inputs, and analysis rules in executable Python. The replacement
uses typed configuration and rejects unknown fields.

Process settings such as listen addresses, data paths, worker count, and proxy
limits belong to one versioned OWTF configuration file. Command flags override
environment variables, which override that file, which overrides compiled
defaults. Settings that require restart are reported as such; they are not
pretended to hot-reload.

Plugin requirements, commands, external references, HTTP probes, and analysis
rules belong to the corresponding ``plugin.yaml``. Per-run values are validated
against the plugin's declared inputs and copied into the immutable task launch
record. Plugin order and named launch selections remain OWTF profiles rather
than becoming global settings.

``owtf config show`` prints effective, redacted settings and ``owtf config
validate`` checks a file without starting OWTF. A later configuration API may
expose the same typed, non-secret values for the UI. Secrets are supplied by
environment or private files, are redacted from output, and are never stored in
SQLite. Legacy database, account, JWT, SMTP, Sentry, and separate UI-server
settings are removed rather than carried forward.

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

Phase 5: feature parity
  Compare the replacement against the legacy OWTF operator workflows before
  adding AI or the product UI. Close gaps in target intake, plugin discovery and
  ordering, individual and group launches, worklist, workers, logs,
  cancellation, proxy, transactions, reports, exports, configuration, and help.
  Account for every legacy plugin variant while preserving ``<code>-<type>``
  IDs. Prefer shared declarative implementations for external resources,
  transaction grep, and HTTP probes; use command or container runtimes only
  where a maintained tool is required. The gate is a reviewed feature matrix,
  a checked plugin inventory in which every variant is runnable or has a
  specific unsupported reason, and CLI/API outcome tests for each retained
  workflow.

Phase 6: AI design
  Define operator workflows, trust boundaries, evidence provenance, threat
  model, model boundaries, and evaluation criteria before selecting features or
  architecture. No AI capability ships merely to satisfy this phase name.

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

Feature parity means observable OWTF outcomes, not implementation parity. The
removed account system, Python runtime, and unsupported installation paths are
explicit non-goals and do not return through the parity work.

The feature matrix is an inventory, not an implementation backlog. A
``missing`` row records an old observable behavior so it can be judged rather
than forgotten. It is implemented only when it remains useful to OWTF's target,
plugin, worklist, proxy, evidence, or reporting workflows. Redundant UI-era
plumbing, unsafe mutable state, and behavior already provided more simply by a
retained workflow are marked ``removed`` or ``replaced`` instead.

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
and SOCKS5 upstream proxies. Basic and Digest target authentication is scoped
  to configured hosts and loaded from a private file. Priority-ordered static
  request and response interceptors provide bounded URL, header, body, and delay
  actions. A separate loopback proxy API listener provides transaction history,
  filters, statistics, clearing, CA download, and request replay through the
  same proxy path. WebSocket traffic is forwarded unchanged and captured as a
  bounded, binary-safe frame transcript. Live interceptors remain before the
  phase gate.

Phase 5 has a checked feature matrix, typed configuration shared by server and
proxy startup, deterministic named plugin profiles, target scope and bounded
search, complete session deletion, typed plugin inputs, and bounded persisted
transaction search. Per-target URL catalogs canonically deduplicate plugin
discoveries and retained traffic, preserve the established visited and scope
fields, and support bounded search through the API and CLI. Tasks retain
ordered attempt history for normal execution
and restart recovery. Failed and cancelled tasks remain terminal; an operator
creates a new run when a technique must be repeated. Declarative external
plugins retain curated manual guidance without sending target traffic, and
declarative grep plugins retain evidence-linked transaction matches. Operators
can assign the established OWTF rank and notes to terminal plugin output; that
mutable review remains separate from scanner evidence and appears in target,
session, CLI, API, and portable reports.
Configuration validation, default/file/environment/flag precedence, bounded
worker and proxy limits, secret redaction, profile validation, persisted run
ordering, deletion conflicts, target pagination, input validation, immutable
snapshots, shell-free argument expansion, transaction ownership, filtering,
and pagination are covered by tests. The remaining matrix rows are not implied
complete by this slice.

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
