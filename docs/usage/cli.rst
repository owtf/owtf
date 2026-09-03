OWTF CLI
=============

The command line is the primary operator and automation interface. It calls the
same HTTP API as other clients and prints JSON to standard output. Diagnostics
go to standard error, so output can be passed directly to tools such as
``jq``.

Start the local OWTF server::

  owtf serve

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
  owtf targets delete tgt_ID

Launch plugins
--------------

List ready and unavailable plugins before launching work. Filters use OWTF's
established plugin group and type names::

  owtf plugins list
  owtf plugins list --group web --type semi_passive

Create a run from existing target IDs. ``--target`` and ``--plugin`` may be
repeated or supplied as comma-separated IDs::

  owtf runs create \
    --session ses_ID \
    --target tgt_ID \
    --plugin OWTF-IG-004-semi_passive \
    --plugin OWTF-WSP-001-active

Launch an OWTF plugin group by group and type. Omit ``--type`` (or use
``--type all``) for every type in the group. ``--type quiet`` retains the old
OWTF meaning of ``passive`` plus ``semi_passive``::

  owtf runs create \
    --session ses_ID \
    --target tgt_ID \
    --group web \
    --type quiet

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
  owtf tasks logs tsk_ID
  owtf tasks cancel tsk_ID

Evidence and reports
--------------------

Target reports retain tasks, logs, observations, findings, transactions, and
artifact metadata::

  owtf targets report tgt_ID
  owtf sessions report ses_ID
  owtf transactions list --session ses_ID --target tgt_ID
  owtf transactions list --target tgt_ID
  owtf transactions import --target tgt_ID capture.har
  owtf transactions show --target tgt_ID txn_ID
  owtf transactions delete --target tgt_ID txn_ID
  owtf artifacts get --output response-body.bin art_ID

HAR import attaches transactions directly to the selected target. It does not
create a plugin run, worklist task, or worker activity. OWTF retains the source
HAR plus non-empty request and response bodies as downloadable files. A single
import is limited to 64 MiB and 10,000 transactions.

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
JSON before accepting traffic. Trust the generated CA only in a dedicated test
browser or tool profile. ``--target-host`` may be repeated; omit it only for an
interactive proxy that intentionally accepts every host.

The proxy retains at most 10,000 transactions and captures at most 1 MiB per
request or response by default. Its bounded response cache excludes OWTF's
historical analytics-cookie list from cache identity. Use ``--cache-entries 0``
to disable caching. Failed requests and HTTP 408/599 responses get at most three
attempts.

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

Run ``owtf help`` for the compact command index. The CLI never opens the
SQLite database or starts plugin processes itself; all state transitions pass
through the server API.
