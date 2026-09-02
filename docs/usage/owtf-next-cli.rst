OWTF Next CLI
=============

The command line is the primary operator and automation interface. It calls the
same HTTP API as other clients and prints JSON to standard output. Diagnostics
go to standard error, so output can be passed directly to tools such as
``jq``.

Start the local control plane::

  owtf-next serve

Commands connect to ``http://127.0.0.1:8009`` by default. Set ``OWTF_URL`` or
pass the global ``--url`` option when the server listens elsewhere::

  export OWTF_URL=http://127.0.0.1:8009
  owtf-next health

Sessions and targets
--------------------

An OWTF session is a named scan workspace, not an authenticated user session::

  owtf-next sessions create --name "Internal web review"
  owtf-next sessions list
  owtf-next targets add --session ses_ID https://example.test
  owtf-next targets list --session ses_ID
  owtf-next targets delete tgt_ID

Launch plugins
--------------

List ready and unavailable plugins before launching work::

  owtf-next plugins list

Create a run from existing target IDs. ``--target`` and ``--plugin`` may be
repeated or supplied as comma-separated IDs::

  owtf-next runs create \
    --session ses_ID \
    --target tgt_ID \
    --plugin OWTF-IG-004-semi-passive \
    --plugin OWTF-WSP-001-active

The ``scan`` convenience command accepts target values directly. It uses the
newest session or creates ``Default session`` when ``--session`` is omitted::

  owtf-next scan \
    --plugin OWTF-IG-004-semi-passive \
    --plugin OWTF-WSP-001-active \
    https://example.test

Inspect and control work
------------------------

Use the persisted worklist for task state and the worker view only for live
executor state::

  owtf-next worklist --session ses_ID
  owtf-next workers
  owtf-next tasks show tsk_ID
  owtf-next tasks logs tsk_ID
  owtf-next tasks cancel tsk_ID

Evidence and reports
--------------------

Target reports retain tasks, logs, observations, findings, transactions, and
artifact metadata::

  owtf-next targets report tgt_ID
  owtf-next transactions list --session ses_ID --target tgt_ID
  owtf-next artifacts get --output response-body.bin art_ID

Run ``owtf-next help`` for the compact command index. The CLI never opens the
SQLite database or starts plugin processes itself; all state transitions pass
through the server API.
