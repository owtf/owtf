# UI implementation and verification

This is a coverage record, not an assertion of complete Python-era parity.
React, TanStack Query and shared shadcn primitives implement the browser UI.
Mutation retries are disabled. Tests use local, approved targets only.

## Implemented

- Sessions: create, select, report, filtered export and confirmed deletion.
- Targets: add, search, scope, selection, deletion and grouped host reports.
  Exact hosts group across URL paths/ports within one session. Subdomains and
  sessions remain separate. URL IDs, execution inputs, scope and evidence are
  preserved; grouping does not rewrite historical targets or expand scope.
- Plugins: individual/group selection, profiles, availability, typed inputs and
  help; original Run labels. Repeated executions have independent evidence and
  review records inside plugin report accordions.
- Worklist/workers: real states and metrics, logs/attempts, pause, resume, order,
  cancellation and pending-task removal. No fabricated progress or retries.
- Reports: severity, disposition, notes, append-only review history, filters,
  artifacts and HTTP evidence links. Accordion tints follow reviewed severity.
- Proxy: retained transactions and live history, search, statistics, HAR import,
  deletion, CA download, repeater, static rules and live request/response
  interception with Continue/Drop. Shared controls use a fixed loopback bridge.
- HTTP inspectors: Request/Response and Headers/Body tabs, bounded retained-body
  previews, downloads and an expandable non-modal right panel. Captured HTML
  is displayed as text, never executed.
- Settings: redacted startup configuration and shared-parser validation. Browser
  validation does not apply configuration or restart processes.
- Supporting pages: profiles, runs, discovered URLs and methodology/help.

## Runtime capture

Compose starts the backend and proxy together. Only proxy traffic is published;
its control API remains loopback-only. `OWTF_PLUGIN_PROXY` explicitly routes
collectors, including loopback targets. `OWTF_PLUGIN_PROXY_CA` adds proxy trust
without disabling TLS verification. Proxy-aware host commands receive standard
proxy and CA environment variables.

Capture to target explicitly chooses an in-scope URL target. Matching-origin
traffic is saved directly to SQLite and the artifact store, without HAR export
or import. The destination is snapshotted before forwarding; switching it cannot
move an in-flight exchange. Other origins stay in shared history. Stop affects
new requests; restarting disables attachment. Persistence failures appear in
capture status and proxy logs rather than silently claiming success.

This is not transparent network enforcement: raw socket tools, tools ignoring
proxy variables and isolated container plugins are not forcibly routed through
an HTTP proxy. Browser proxy configuration is external to the OWTF page.

## Evidence (2026-09-04)

- Type checking, 42 frontend tests, production UI build and `go test ./...` pass.
- Test session `ses_b95b50a061beae600c3ff775` contains the real local lab on
  `host.docker.internal:18680`, collection/grep executions, captured responses,
  artifacts and a browser-saved low/confirmed cookie review.
- A collector run appeared in live proxy history after automatic routing was
  enabled. Explicit curl traffic attached directly to the selected target;
  traffic sent after Stop did not. Evidence: `build/ui-full-flow/`.
- Browser verified session/target creation, plugin launch, logs, review save,
  request edit/Continue, response status edit/Continue (202), Drop (403),
  pause/resume, cancellation, reordered paused tasks and confirmed removal (404).
- Browser verified actual response headers and body in the new tabs, and
  expanding/restoring a right-hand log panel. Screenshots were rendered live.
- Same-host report API combined two real local URL targets. Tests cover session
  and subdomain separation and preservation of out-of-scope URL state.
- Export ZIP integrity passed. Compose recovery verification covers repeated
  runs with separate reviews, cancellation, restart, backup/restore and artifact
  hashes. `scripts/owtf-compose-smoke.sh` now includes automatic capture.
- `scripts/owtf-proxy-ui-smoke.sh` covers rule effects, request/response handling,
  timeout release, CA, HAR import/show/delete and session cleanup with real HTTP.

## Remaining verification and boundaries

- Native browser HAR file selection and phone-sized layout have not been
  exercised live with the available IAB controls. API HAR import and the form's
  multipart behavior are tested; that is not native-picker evidence.
- Layout follows the target/sidebar/accordion design and later user overrides,
  but has not received a complete pixel-by-pixel mockup comparison.
- Host grouping is a read model over stable URL targets, not a destructive schema
  migration. CLI target IDs and existing report/export formats remain usable.
- Process-only actions (server start, trust installation, container tool setup)
  remain CLI/Compose responsibilities, not simulated browser operations.
