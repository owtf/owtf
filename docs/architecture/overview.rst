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

Plugin source is organized by stable OWTF technique code and variant::

  plugins/
    OWTF-IG-004/
      semi-passive/
        plugin.yaml
    OWTF-WSP-001/
      active/
        plugin.yaml

The manifest ID includes both parts, such as
``OWTF-IG-004-semi-passive``. The directory is for maintainers; the manifest
remains the runtime source of truth and the catalog discovers it recursively.

Core model
----------

``Session``
  Named body of work containing targets, runs, evidence, and reports.

``Target``
  A normalized URL, hostname, IP address, or CIDR. Duplicate values within an
  session are rejected.

``Plugin``
  A versioned manifest for one executable technique. IDs use the existing code
  plus a variant where needed, for example ``OWTF-WSP-001-active``.

``Run`` and ``Task``
  A run is an immutable launch plan. Each target/plugin pair becomes a durable
  task with attempts, timestamps, terminal status, and an explicit error.

``Event``
  Ordered lifecycle, stdout, and stderr output attached to a task attempt.

``HTTPExchange`` and ``Artifact``
  Captured request/response metadata and immutable raw evidence. Artifacts are
  addressed by SHA-256 rather than by mutable report paths.

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
3. Launch one plugin, a selected set, or a named profile against selected
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
codes, variant, runtime, requirements, and supported target kinds.

The first runtime is a Go builtin used to prove the contract. The next runtime
is a local command expressed as an executable plus an argument array. Target and
configuration values are passed as individual arguments or environment values;
they are never interpolated into shell source. A strict shell runtime may be
added later only if its parsed syntax can reject dynamic commands, ``eval``,
``source``, command substitution, and ``sh -c`` before execution.

Missing required executables make a plugin unavailable before a run starts.
Optional plugins may be skipped only when the plan and UI record the reason.
Plugins do not open SQLite or call internal Go packages.

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
  intake, plugin and profile launches, worklist, workers, logs, cancellation,
  transactions, evidence, reports, and portable exports. The CLI calls the same
  HTTP API and emits scriptable JSON. The gate is a complete CLI-driven scan and
  an offline report opened without the server.

Phase 4: evidence import
  Integrate a maintained proxy such as mitmproxy or ZAP and import HAR/evidence.
  OWTF does not maintain a new TLS interception stack unless external tools
  prove insufficient under a separate design review.

Phase 5: AI assistance
  Add optional evidence search and AI summaries that cite stored observations
  and artifacts. Human-reviewed findings remain authoritative.

Phase 6: operator UI
  Build the final React and TypeScript interface with Tailwind and shadcn
  primitives, compact Inter typography, and complete parity with the CLI. Every
  screen uses the real API; no demo counters or simulated progress. The current
  embedded interface is disposable proof tooling, not the product UI.

Phase 7: legacy retirement
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
``OWTF-IG-004-semi-passive``. Automated tests also verify missing-command
visibility, non-shell argument handling, task cancellation, and termination of
the complete plugin process group, including a child that ignores the initial
termination signal.

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
