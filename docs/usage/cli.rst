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

Run ``owtf help`` for the compact command index. The CLI never opens the
SQLite database or starts plugin processes itself; all state transitions pass
through the server API.
