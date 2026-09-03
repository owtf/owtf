OWTF CLI
=============

The command line is the primary operator and automation interface. It calls the
same HTTP API as other clients and prints JSON to standard output. Diagnostics
go to standard error, so output can be passed directly to tools such as
``jq``.

Start the local OWTF server::

  owtf serve

Configuration
-------------

OWTF reads ``.owtf/config.yaml`` when it exists. A different file may be
selected with ``OWTF_CONFIG`` or ``--config``. Unknown fields and unsupported
schema versions fail before a listener or worker starts::

  owtf config validate .owtf/config.yaml
  owtf config show --config .owtf/config.yaml

``config show`` prints the effective configuration as JSON after environment
overrides and redacts credentials. Startup precedence is command flags,
environment variables, the configuration file, then compiled defaults.

A minimal file may override only the required settings::

  apiVersion: owtf.dev/v1alpha1
  kind: Config
  server:
    address: 127.0.0.1:8009
    dataDirectory: .owtf
    workers: 1
    taskTimeoutSeconds: 300
  plugins:
    directory: plugins
    profilesDirectory: profiles
    defaultProfile: default
    containerEngine: docker
  proxy:
    listenAddress: 127.0.0.1:8008
    apiAddress: 127.0.0.1:8010
    targetHosts: [example.test]

Server flags are ``--addr``, ``--data-dir``, ``--workers``, ``--plugin-dir``,
``--profile-dir``, ``--profile``, ``--container-engine``, and
``--task-timeout``. Existing ``OWTF_ADDR``, ``OWTF_DATA_DIR``,
``OWTF_WORKERS``, ``OWTF_PLUGIN_DIR``, ``OWTF_PROFILE_DIR``, ``OWTF_PROFILE``,
and ``OWTF_CONTAINER_ENGINE`` variables remain supported;
``OWTF_TASK_TIMEOUT`` is an integer number of seconds. Proxy YAML fields
correspond to the documented proxy flags. Their environment names use the
``OWTF_PROXY_`` prefix, such as ``OWTF_PROXY_LISTEN``,
``OWTF_PROXY_API_LISTEN``, ``OWTF_PROXY_MAX_BODY``, and
``OWTF_PROXY_TARGET_HOSTS``. Comma-separated environment values are used for
cookie lists and target hosts.

Do not put credentials in YAML. Supply an authenticated upstream proxy through
``OWTF_PROXY_UPSTREAM`` and target HTTP credentials through a private file.
Configuration is startup-only in this phase; it is not stored in SQLite and
does not pretend to hot-reload.

Commands connect to ``http://127.0.0.1:8009`` by default. Set ``OWTF_URL`` or
pass the global ``--url`` option when the server listens elsewhere::

  export OWTF_URL=http://127.0.0.1:8009
  owtf health

Sessions and targets
--------------------

An OWTF session is a named scan workspace, not an authenticated user session::

  owtf sessions create --name "Internal web review"
  owtf sessions list
  owtf targets add --session ses_ID https://example.test
  owtf targets list --session ses_ID
  owtf targets search --session ses_ID --search example --kind url --scope true
  owtf targets update --scope false tgt_ID
  owtf targets delete tgt_ID
  owtf sessions delete ses_ID

Target search returns ``records_total``, ``records_filtered``, and a bounded
``data`` page. The default limit is 100 and the maximum is 1000. Target and
session deletion reject queued or running work; cancel that work first.

Launch plugins
--------------

List ready and unavailable plugins before launching work. Filters use OWTF's
established plugin group and type names::

  owtf plugin list
  owtf plugin list --group web --type semi_passive

``plugin list`` returns each type-specific implementation with its established
OWTF code, title, hint, priority, and reference. Each task snapshots that
metadata so later manifest edits do not rewrite historical reports. There is no
separate technique command.

Run an external plugin to retain manual testing guidance without contacting the
target::

  owtf scan \
    --session SESSION_ID \
    --plugin OWTF-IG-004-external \
    https://example.test

Run a grep plugin after traffic has been captured or imported::

  owtf runs create \
    --session SESSION_ID \
    --target TARGET_ID \
    --plugin OWTF-IG-004-grep

List profiles or inspect their plugin order::

  owtf profiles list
  owtf profiles show default

Create a run from existing target IDs. ``--target`` and ``--plugin`` may be
repeated or supplied as comma-separated IDs::

  owtf runs create \
    --session ses_ID \
    --target tgt_ID \
    --plugin OWTF-IG-004-semi_passive \
    --plugin OWTF-WSP-001-active \
    --input OWTF-IG-004-semi_passive.timeout_seconds=30 \
    --input 'OWTF-IG-004-semi_passive.user_agent=OWTF review'

``--input`` is repeatable and uses ``PLUGIN_ID.NAME=VALUE``. OWTF validates the
value against the plugin schema, resolves defaults, and records the resulting
non-secret values with each task. Do not pass passwords, tokens, or other
secrets through plugin inputs.

Run the retained FTP service probe against an existing hostname or IP target::

  owtf runs create \
    --session ses_ID \
    --target tgt_ID \
    --plugin PTES-001-active \
    --input PTES-001-active.port=21

This plugin requires ``nmap``. If the executable is absent, ``plugin list``
keeps the plugin visible with ``missing_requirements`` and OWTF rejects an
individual launch before creating work.

Launch an OWTF plugin group by group and type. Omit ``--type`` (or use
``--type all``) for every type in the group. ``--type quiet`` retains the old
OWTF meaning of ``passive`` plus ``semi_passive``::

  owtf runs create \
    --session ses_ID \
    --target tgt_ID \
    --group web \
    --type quiet \
    --profile default

The configured default profile applies when ``--profile`` is omitted. A
profile orders matching plugins; it does not exclude matching plugins that are
not listed. Those plugins follow in stable ID order. OWTF records the selected
profile on the immutable run.

List completed and active plugin runs, or inspect one run::

  owtf runs list --session ses_ID
  owtf runs show run_ID

The ``scan`` convenience command accepts target values directly. It uses the
newest session or creates ``Default session`` when ``--session`` is omitted::

  owtf scan \
    --group web \
    --type semi_passive \
    https://example.test

Inspect and control work
------------------------

Use the persisted worklist for task state and the worker view only for live
executor state::

  owtf worklist --session ses_ID
  owtf workers
  owtf tasks show tsk_ID
  owtf tasks attempts tsk_ID
  owtf tasks logs tsk_ID
  owtf tasks cancel tsk_ID
  owtf tasks pause tsk_ID
  owtf tasks resume tsk_ID
  owtf tasks remove tsk_ID
  owtf worklist reorder --session ses_ID tsk_FIRST tsk_SECOND

Only queued work can be paused. Resume returns paused work to the dispatch
queue. Reorder must name every queued and paused task in the session and changes
their durable dispatch order. Remove accepts only queued, paused, or blocked
tasks; started and terminal work remains part of the report evidence. There is
no retry command: create a new run when deliberate re-execution is appropriate.

Failed and cancelled tasks are terminal. To repeat a technique, create a new
run so the worklist retains a distinct task and clear execution provenance.
Use ``tasks attempts`` to inspect execution history, including interrupted work
recovered after a server restart; ``tasks logs`` keeps every event linked to
its attempt ID.

Help links
----------

List OWTF's curated exploitation, methodology, calculator, learning, and
project references::

  owtf help list

The catalog is compiled into the OWTF binary, versioned separately from scan
evidence, and never executed or fetched by the server. Invalid or non-HTTPS
links fail catalog validation during tests.

Evidence and reports
--------------------

Target reports retain tasks, attempts, logs, observations, findings,
URLs, transactions, plugin output reviews, and artifact metadata::

  owtf targets report tgt_ID
  owtf sessions report ses_ID
  owtf plugin review tsk_ID
  owtf plugin review --rank high --notes "Verified manually" tsk_ID
  owtf urls list --target tgt_ID
  owtf urls search --target tgt_ID --search login --visited true --scope true
  owtf transactions list --session ses_ID --target tgt_ID
  owtf transactions list --target tgt_ID
  owtf transactions search --session ses_ID --search login --method POST --status 401
  owtf transactions search --target tgt_ID --limit 50 --offset 100
  owtf transactions import --target tgt_ID capture.har
  owtf transactions show --target tgt_ID txn_ID
  owtf transactions delete --target tgt_ID txn_ID
  owtf artifacts get --output response-body.bin art_ID

Plugin output reviews are operator decisions stored separately from immutable
scanner evidence. Valid ranks are ``unranked``, ``passing``,
``informational``, ``low``, ``medium``, ``high``, and ``critical``. Running
``plugin review`` without review flags reads the current value. ``--notes=``
clears notes. Only completed, failed, or cancelled tasks can be reviewed.

Plugins add discovered HTTP and HTTPS URLs to the owning target's URL catalog;
retained transactions add their URLs automatically. Repeated discoveries are
canonically deduplicated. ``visited`` records whether traffic was retained and
``scope`` uses the target's exact host or IP network. Deleting a transaction
does not erase its URL catalog entry; deleting the target does. URL search is
case-insensitive and supports ``visited``, ``scope``, ``limit``, and ``offset``
filters.

HAR import attaches transactions directly to the selected target. It does not
create a plugin run, worklist task, or worker activity. OWTF retains the source
HAR plus non-empty request and response bodies as downloadable files. A single
import is limited to 64 MiB and 10,000 transactions.

``transactions search`` matches URL, method, request headers, and response
headers without loading retained bodies. Results include ``records_total``,
``records_filtered``, and a deterministic newest-first page. The default page
size is 100 and the maximum is 1,000. Captured transactions are immutable;
send a modified request through ``owtf proxy repeat`` instead of rewriting
source evidence.

Export a complete session report for offline review. The ZIP contains JSON,
an HTML report, a manifest, and the retained artifact files::

  owtf sessions export --output session-report.zip ses_ID

Capture HTTP transactions
-------------------------

Start the OWTF interception proxy on its historical loopback port. On clean
shutdown it writes a standard HAR file that can be imported into a target::

  owtf proxy \
    --target-host example.test \
    --output .owtf/proxy/capture.har

The command prints its listen address, CA certificate path, and output path as
JSON before accepting traffic. It also prints the proxy API address, which
defaults to ``127.0.0.1:8010``. Trust the generated CA only in a dedicated test
browser or tool profile. ``--target-host`` may be repeated; omit it only for an
interactive proxy that intentionally accepts every host. Keep the proxy and API
listeners on loopback unless a trusted reverse proxy protects them.

The proxy retains at most 10,000 transactions and captures at most 1 MiB per
request or response by default. Its bounded response cache excludes OWTF's
historical analytics-cookie list from cache identity. Use ``--cache-entries 0``
to disable caching. Failed requests and HTTP 408/599 responses get at most three
attempts.

WebSocket upgrades remain byte-for-byte tunnels. When a connection closes, its
bounded frame transcript becomes the transaction response body with media type
``application/vnd.owtf.websocket+json``. Payloads are base64 encoded and retain
their direction, opcode, framing flags, and protocol errors. Importing the HAR
into a target retains that transcript as a response artifact.

Route outbound traffic through another proxy when required::

  owtf proxy --upstream http://user:password@proxy.test:8080
  owtf proxy --upstream socks5://user:password@proxy.test:1080

HTTP, HTTPS, and SOCKS5 upstream URLs are supported. Credentials are supplied
only through URL user information and are never interpolated into shell text.

Target HTTP authentication is separate from OWTF access control. Put Basic or
Digest credentials in a private JSON file and pass its path to the proxy::

  chmod 600 target-auth.json
  owtf proxy --http-auth-file target-auth.json

The file maps target hosts to credentials::

  {
    "example.test": {
      "username": "test-operator",
      "password": "test-password"
    }
  }

OWTF sends credentials only after a listed host returns a supported Basic or
Digest challenge. The file must be regular, smaller than 64 KiB, and
inaccessible to group and other users.

Apply deterministic request and response transformations with a JSON rule
file::

  owtf proxy --interceptor-file interceptors.json

Rules run from the lowest priority number to the highest. Omitted ``enabled``
values default to true. Matches may constrain the request URL, method, and
content type; actions may rewrite a request URL, set, add, or remove headers,
replace, prepend, or append body text, and introduce a bounded delay::

  {
    "rules": [
      {
        "name": "mark-requests",
        "priority": 10,
        "phase": "request",
        "match": {
          "url_pattern": "example\\.test",
          "methods": ["GET", "POST"]
        },
        "action": {
          "set_headers": {"X-OWTF": "captured"}
        }
      },
      {
        "name": "redact-text",
        "priority": 20,
        "phase": "response",
        "match": {"content_types": ["text/plain"]},
        "action": {
          "body_replace": [
            {"pattern": "secret", "replacement": "[redacted]"}
          ]
        }
      }
    ]
  }

Configuration is capped at 1 MiB and 100 rules. Body changes use
``--max-body`` as a hard limit, reject encoded content, and are not applied to
WebSocket streams. Response rules are skipped for WebSocket upgrades. URL
rewrites are checked against ``--target-host`` after transformation.

Inspect or change the active rules without restarting the proxy::

  owtf proxy interceptors list
  owtf proxy interceptors disable redact-text
  owtf proxy interceptors enable redact-text
  owtf proxy interceptors replace interceptors.json

Replacement validates and compiles the complete document before one atomic
swap. Invalid documents leave the active rules unchanged, and an in-flight
HTTP exchange uses one rule snapshot for both its request and response. Runtime
changes are not written back to ``--interceptor-file`` and end when the proxy
stops.

Inspect and replay proxy traffic
--------------------------------

The proxy API commands use ``http://127.0.0.1:8010`` by default. Override
that address with ``OWTF_PROXY_API_URL`` or ``--api``::

  owtf proxy status
  owtf proxy transactions --method POST --status 200 --search token
  owtf proxy transaction 1
  owtf proxy stats
  owtf proxy ca --output owtf-proxy-ca.crt
  owtf proxy repeat --method POST --header 'Content-Type: application/json' \
    --data '{"probe":true}' https://example.test/api
  owtf proxy clear

``proxy transactions`` returns bounded summaries. ``proxy transaction``
returns raw headers and base64-encoded request and response bodies. Repeater
bodies are also base64-encoded internally so binary data is not coerced; use
``--data-file`` for a binary request and ``--output`` for a binary response.
Repeater requests travel through the running OWTF proxy and therefore use the
same target scope, cache, retry, authentication, interceptors, and capture path.
Clearing history releases the in-memory capture, so cleared entries will not be
present in the HAR written at shutdown.

The same operations are available directly for scripts::

  curl -sS http://127.0.0.1:8010/api/v2/transactions
  curl -sS http://127.0.0.1:8010/api/v2/transactions/stats
  curl -sS http://127.0.0.1:8010/api/v2/transactions/1
  curl -sS http://127.0.0.1:8010/api/v2/ca -o owtf-proxy-ca.crt
  curl -sS -X POST -H 'Content-Type: application/json' \
    --data '{"method":"GET","url":"https://example.test/"}' \
    http://127.0.0.1:8010/api/v2/repeater
  curl -sS http://127.0.0.1:8010/api/v2/interceptors
  curl -sS -X PUT -H 'Content-Type: application/json' \
    --data @interceptors.json http://127.0.0.1:8010/api/v2/interceptors
  curl -sS -X PATCH -H 'Content-Type: application/json' \
    --data '{"name":"redact-text","enabled":false}' \
    http://127.0.0.1:8010/api/v2/interceptors
  curl -sS -X DELETE http://127.0.0.1:8010/api/v2/transactions

Run ``owtf help`` for the compact command index. The CLI never opens the
SQLite database or starts plugin processes itself; all state transitions pass
through the server API.
