# Settings decisions after the migration audit

This records product decisions following the four-file settings inventory. It is
not a list of 252 missing features to implement. Runtime and plugin changes are
separate work; the decisions below do not imply they have shipped.

## Verified compatibility differences

| Area | Legacy evidence | Current evidence | Decision |
| --- | --- | --- | --- |
| Task timeout | Pinned `owtf/settings.py` sets `PLUGIN_TIMEOUT=300`; `owtf/plugin/harness.py:execute_with_timeout` wraps the plugin function with SIGALRM and has a platform fallback. | `internal/config/config.go:Default` sets 30 seconds; `internal/runner/runner.go` uses a cancellable context around task execution. | Mark partial compatibility. Keep an explicit configurable whole-task deadline and no automatic retries. Do not silently restore 300 seconds or claim 30 seconds suits every scanner. Revisit the default with retained-tool duration evidence when plugin work resumes. |
| SQL Server | `general.yaml:MSSQL_PORT_NUMBER` is 1434; resources include Metasploit ping, hashdump, and schemadump commands. The port constant alone does not establish the transport used by every old module. | `plugins/network/PTES-006/active/plugin.yaml` uses TCP `-sT`, port 1433, and `ms-sql-info,ms-sql-ntlm-info`. | Keep the explicit unauthenticated TCP probe. Mark legacy discovery/dump parity partial. Do not switch to 1434 merely to match a constant. UDP Browser discovery and authenticated dumps are not implemented by this probe. |
| Fingerprinting | Header list includes Server, X-Powered-By, X-AspNet-Version, X-Runtime, X-Version, and MicrosoftSharePointTeamServices. | `OWTF-IG-004-grep` matches Server/X-Powered-By and generator meta tags. | Partial header coverage; retain the gap until plugin work resumes. |
| CORS | Header list includes Expose-Headers and Max-Age. | `OWTF-WGP-002-grep` matches Allow-Origin/Credentials/Methods/Headers. | Partial coverage. Raw transaction headers are retained, but a missing grep match is not a negative security finding. |
| Cache | Header rules include Expires; body rules include Pragma and Expires meta tags. | `OWTF-AT-007-grep` matches selected Cache-Control directives, Pragma no-cache, and Cache-Control meta tags. | Partial extraction, not equivalent legacy coverage. |
| Cookies | An explicit list of secure/HttpOnly/domain/path/expires attributes exists. | `OWTF-SM-002-grep` locates Set-Cookie headers; it does not implement that attribute-policy analysis. | Keep evidence capture and mark attribute analysis partial. |
| Other body rules | CSS/JS comments, autocomplete and generic hidden-field extraction are configured. | No equivalent general rules were verified. Password-form matching is narrower and HTML-comment matching is bounded. | Preserve gaps; do not add obsolete regexes just to increase parity counts. |

Legacy paths refer to commit `c41908bf0b83c5588f885ee20e5d187bf5d87be2`, not a
verified 2.6.10 release. These are code/configuration comparisons, not live SQL
Server or legacy Python runtime comparisons. No scan was run for this decision pass.

## Implemented global controls

Two typed controls are now implemented and documented in `docs/usage/cli.rst`:

- A process log level (`debug`, `info`, `warn`, `error`), shared by server and proxy.
  It controls OWTF diagnostics, not deletion/filtering of captured task logs.
  Use `logLevel`, `OWTF_LOG_LEVEL`, or `--log-level`.
- Consistent request defaults for OWTF-owned HTTP collectors: User-Agent and
  per-request timeout, bounded by the whole-task deadline. Built-in collectors
  currently use `OWTF/0.1` and 20 seconds; some curl plugins have their own inputs.
  The shared override uses `http.userAgent` and `http.requestTimeoutSeconds`. External scanners keep their explicit
  manifest inputs; do not pretend a global field changes arbitrary tool behavior.

Avoid a general key/value settings API. Use typed fields and documented precedence.
Keep current defaults until a change is implemented and tested; do not introduce
settings which no runtime consumes.

CORS configuration is unnecessary for the shipped deployment: the separate
frontend forwards API requests through the same origin. Encrypted CA-key loading waits for an actual
operational requirement. Neither is a release gate for the current local workflow.

## Explicit retirements

The following are intentionally outside the rewritten OWTF product:

- Persistent remote-shell/RCE connection management, SBD agents/listeners, and
  interactive shell reuse/exit/command-chain orchestration.
- SET integration, phishing campaigns, payload/template generation, listener
  setup, and SMTP mail delivery for those campaigns.

OWTF coordinates tests and retains evidence. Those subsystems add agent/session,
payload, credential, and campaign lifecycles that are better owned by dedicated
operator tools. They will not be recreated merely to match legacy settings.

This retires their configuration and launcher resources. It does not remove
trusted command plugins, normal HTTP target authentication, the SMTP service
probe, or retained manual testing guidance. No runtime files are deleted here:
these retired subsystems were already absent from the Go application.

`REPEAT_DELIM`, `TEST`, and `COMMAND_SUFFIX` belong to the old arbitrary auxiliary
command-chain interface; that interface is retired too. Typed manifest inputs
remain the supported way to parameterize commands.

## Deferred work and maintaining the audit

Dictionaries, reusable port lists, old scanner integrations, grep rules, passive
and active discovery resources, and detailed plugin parity stay deferred. Keep
rows marked `partial` or `gap` when that describes coverage; deferred scheduling
must not turn them into implemented equivalents.

The CSV is a reference for decisions, not an automatically generated backlog.
When behavior changes, update only affected rows, cite the implementation and its
verification, and adjust the summary counts. Preserve source identities/hashes so
coverage can still be checked. Do not add legacy constants with no retained use.

`owtf config show` resolves the invoking process's environment/files. It does not
read a remote server's effective configuration. A future read-only settings API
must make that distinction explicit if the UI needs it.

Verification: `cmd/owtf/logging_test.go` covers diagnostic levels and flag
precedence; `internal/config/config_test.go` covers strict validation;
`internal/plugin/http_config_test.go` uses a local HTTP server to check User-Agent,
request deadlines, shorter task deadlines, and retained evidence.
