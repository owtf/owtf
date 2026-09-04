# Operator UI: legacy research and implementation contract

## Reference, not a runtime parity claim

The reference is the **pre-React Bootstrap interface**, not `owtf/webapp`.
Templates and inline JavaScript were inspected at tag `v2.0a` (commit
`f2d648e1c`; 2016-05-14). Its bundled CSS identifies Bootstrap 3.3.6.
Historical screenshots were recovered from `docs/images` at
`c41908bf0b83c5588f885ee20e5d187bf5d87be2`. They are documentation images,
not screenshots of a legacy server run during this research.

Sources:

- [Original templates](https://github.com/owtf/owtf/tree/v2.0a/framework/interface/templates)
- [Archived screenshots](https://github.com/owtf/owtf/tree/c41908bf0b83c5588f885ee20e5d187bf5d87be2/docs/images)
- [Plugin workflow documentation](https://owtf.readthedocs.io/en/develop/usage/plugins.html)
- [Report documentation](https://owtf.readthedocs.io/en/develop/usage/results.html)
- [2013 Summer Storm presentation](https://www.slideshare.net/slideshow/owasp-owtf-summer-storm-owasp-appsec-eu-2013/25571649)
- [2014 Lionheart UI and Database tour](https://7asecurity.com/blog/2014/10/owtf-10-lionheart-ui-and-database/)

The Lionheart article's embedded screenshots were inspected in the visible
in-app browser. Its report shows compact severity-colored test-code rows;
expanded plugin reports place type tabs, execution details and output links
inside the report, rather than separate dashboard cards. Its launcher uses a
tabbed selection table in a modal. Preserve these structural patterns with
accessible controls, not the old CSS or unsafe overwrite behavior. These are
historical reference images, not proof of the new implementation working.

The 2013 presentation describes the reporting redesign goals and prototypes; it
is not evidence that every later Bootstrap screen shipped in 2013. The 2019
Medium article was not retrievable and is not used to establish behavior.

## What the old UI looked like and did

| Screen | Verified layout and interaction | Source templates / screenshot |
| --- | --- | --- |
| Navigation | Compact horizontal dark navbar; Targets, Workers, Worklist, Settings, PlugnHack, Help. Most screen area is working data, not dashboard cards. | `base.html`; `worklist_manager_mixed.png` |
| Targets | Multiline intake, session control, export and run toolbar; searchable table with checkboxes, target links, severity, row actions, selection count and bulk actions. | `target_manager.html`; `target_table_selected.png` |
| Plugin launcher | Shared modal opened from selected targets or one report. Individual/group tabs; checkbox table with Code, Name, Type, Group, Help; search, pagination and Run footer. Group tab selects group/type sets. | `plugin_launcher.html`; `plugin_launch_individual.png` |
| Target report | URL and severity header, Filter/Refresh/Run Plugins/Logs toolbar. Full-width collapsible test-code rows show title and hint. Inside each row, tabs separate plugin types. | `target.html`, `plugin_report.html`; `target_report.png`, `test_code_report.png` |
| Output review | Rank controls, runtime/time/status, output-file links and notes alongside results; report header severity styling updates after ranking. References remain close to the test code. | `plugin_report.html` |
| Worklist | Compact table, target links, plugin group/type/name, timing and state-dependent controls; bulk pause/resume/remove. Search and pagination rather than one large card per task. | `worklist_manager.html`; `worklist_manager_mixed.png` |
| Workers | Separate worker view with control intent for pause/resume/abort and periodic refresh. The inspected template includes incomplete display code: do not copy its implementation as proof of working behavior. | `worker_interface.html` |
| Transactions | Searchable method/status/URL/timing table; request, response headers and body inspection; previous/next navigation and explicit replay. | `transaction_log.html`, `transaction.html`, `replay_request.html` |

The report, not an analytics dashboard, is the main review surface. Preserve
that hierarchy. Keep dense readable tables, modest controls and Inter. Use
neutral surfaces and borders; reserve severity colors for meaning. Do not copy
old gradients, oversized headers or icon-only controls without accessible labels.

## Translate behavior, not obsolete contracts

- Keep test codes and plugin-type tabs. Group using returned plugin metadata,
  not guessed parsing of IDs. Show execution history per plugin without
  collapsing older evidence into a single overwritten result.
- Replace Force Overwrite with an explicit new run preserving prior evidence.
  Never automatically retry a launch or replay after an ambiguous failure.
- OWTF sessions are collections of work, not accounts. The old report's
  **User Sessions** button inspected target cookies; it was not the OWTF session
  picker. Do not restore login or invent cookie-management parity.
- Current pause/resume endpoints govern queued/paused tasks, not OS process
  suspension. Running work offers cancellation. Worker controls must act on the
  actual task and expose only supported transitions.
- The old remove-from-session and delete-everywhere distinction does not map
  directly to the current target ownership model. Show only supported deletion
  semantics, including evidence loss, with explicit confirmation.
- No fabricated completion percentage or estimated remaining time. Display
  actual states, counts and measured duration. A completed tool is not a passing
  security result.
- Keep review rank, notes, disposition and append-only history. Never inject old
  scanner HTML into the app DOM; escape text and isolate untrusted artifacts.
- Do not restore PlugnHack, Zest scripting, rich-text editor machinery, arbitrary
  settings editing or old account flows merely because a screenshot has them.

## Minimal implementation

React + TypeScript + TanStack Query + selected shadcn/ui components, styled with
Tailwind. No Redux, RTK Query, sagas, Bootstrap runtime, TanStack Table or generic
component factories. Plain semantic tables are sufficient initially. Use local
React state for forms and selection; use a URL session identifier for shareable
context. Configure mutation retries off. Poll reads only while needed and stop
polling when the page is hidden/unmounted.

Reuse current Go endpoints, models, bundled Inter, artifact/report services and
API tests. Build static assets and embed them in the Go binary; no separate
production frontend server. Keep endpoint definitions together and feature code
beside its page. Copy only needed shadcn components with their license notices;
[shadcn distributes component source](https://ui.shadcn.com/docs), so its updates
remain our maintenance responsibility.

## Build order and gates

1. Session selection, target table/intake, shared plugin launcher and target
   report accordions. Existing APIs: sessions, targets/search, plugins, profiles,
   runs, target report, task review/history, artifacts and session export.
2. Worklist and workers: task states, events, cancellation, queued pause/resume,
   removal and ordering. Reuse tasks, workers, metrics and worklist/order APIs.
3. Transactions and report review polish: request/response inspection, filters,
   notes/disposition/history and exports. Proxy replay uses the separate proxy
   API; settle same-origin routing before adding a replay control. Do not silently
   send requests to an unrelated proxy process.
4. Help and supported settings presentation. There is no general server-settings
   read/edit API today; `config show` is local-process configuration, not that API.

For each slice, use a fresh Docker instance and an owned local target. Verify
with curl and the in-app browser: target intake, exact launch selection, durable
work state, logs, report evidence and restart persistence. Exercise empty/error
states, unavailable plugins, cancellation and narrow-screen/keyboard interaction.
Save screenshots of the real application before calling the slice complete.
The recovered historical screenshots are design references, not acceptance proof.


## Implementation evidence (2026-09-04)

The first React implementation covers the four slices above, except proxy
replay, which remains intentionally absent. It reuses the existing Go API.

Verified in a visible IAB tab against the real Docker service on port 18309:

- Create a session; add localhost target with duplicate and invalid input.
- Search the shared launcher and explicitly run `OWTF-WSP-001-active`.
- Observe succeeded work, inspect ordered logs, save review notes.
- Expand target test-code accordion, plugin-type tab, and execution details.
- Inspect captured transaction request/response headers.
- Observe a running cancellation fixture in Workers and cancel it explicitly.
- Select and delete a disposable target; its API subsequently returned 404.

Curl checks independently verified review history, queue pause/resume/order/
removal, cancellation, exported report with body artifact, and persistence after
service restart. A process check inside the container found no orphan `sleep`
process after browser cancellation. The localhost fixture generated real traffic;
no public target was scanned. Historical screenshots were not used as proof.

Frontend regression tests cover launch selection, unavailable tools, typed
inputs, failed mutations without retries, task controls, reviews, escaped
transaction content, empty sessions, and API failures. Go tests also check UI
routes and generated asset references. Runtime screenshots were shown inline in
the task. Local curl outputs and report ZIP are under `build/react-ui-proof/`.

Not claimed: complete legacy parity, Kali tool execution in this proof instance,
proxy replay UI, runtime settings editing, or a mobile-device acceptance run.

Final checks: 12 frontend tests passed; TypeScript and production Vite build
passed; `go test ./...`, `go vet ./...`, and `go test -race ./internal/api`
passed. The final production report was reopened in IAB after the rebuild and
its long-URL toolbar layout was visually rechecked.
