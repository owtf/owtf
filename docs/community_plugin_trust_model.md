# Community Plugin Marketplace: Trust Model

This document spells out who can do what in the community plugin
marketplace, and what the marketplace does NOT protect against. If you
are reviewing pull requests that touch plugin upload, approval, or the
runner, read this first so the assumptions are on the record.

## Roles

There are exactly two roles.

- **Regular user.** Anyone who has a valid OWTF account and an
  unexpired JWT. Regular users can upload plugins, browse the approved
  catalogue, see their own uploads (including rejection reasons), and
  run their own scans. They cannot see other users' uploads, cannot
  see any plugin's source code, and cannot approve, reject, delete,
  test-run, or read the audit log of any plugin.
- **Admin.** A user with `users.is_admin = TRUE` in the database, or
  whose email appears in the `OWTF_ADMIN_EMAILS` env var at server
  start. Admins can review source, approve, reject, delete, test-run,
  and read the audit log. Admins are the trust boundary for the whole
  marketplace: an approved plugin runs with the same permissions as a
  built-in OWTF plugin.

Admins can be seeded via `OWTF_ADMIN_EMAILS` (a comma-separated list of
emails) or managed at runtime with the `owtf-admin` CLI:

```
owtf-admin promote reviewer@example.com
owtf-admin demote  reviewer@example.com
owtf-admin list
```

There is no default admin email. If `OWTF_ADMIN_EMAILS` is empty and
nobody has been promoted, the marketplace has no admins and no plugin
will ever be approved. That is intentional; a hard-coded default is a
credential leak waiting to happen.

## Endpoint exposure

| Endpoint                                              | Role     | Notes                                              |
| ----------------------------------------------------- | -------- | -------------------------------------------------- |
| `POST /api/v1/community-plugins/upload`               | user     | AST-validated at upload time.                      |
| `GET  /api/v1/community-plugins/`                     | user     | Approved-only. Non-admins get 403 on `?status=pending` / `?status=rejected`. |
| `GET  /api/v1/community-plugins/<id>/`                | user     | Public metadata. No `file_path`, no `source_code`. |
| `GET  /api/v1/community-plugins/mine/`                | user     | User's own uploads with rejection reasons.         |
| `GET  /api/v1/community-plugins/me/`                  | user     | Current user's `{id, name, email, is_admin}`.      |
| `GET  /api/v1/community-plugins/<id>/source/`         | admin    | Reads file server-side; response never carries `file_path`. |
| `DELETE /api/v1/community-plugins/<id>/delete/`       | admin    | Removes the DB row and the file on disk.           |
| `POST /api/v1/community-plugins/<id>/test-run/`       | admin    | Rate-limited, non-persistent, admin-only smoke test. |
| `POST /api/v1/community-plugins/<id>/approve/`        | admin    | Records reviewer id + timestamp.                   |
| `POST /api/v1/community-plugins/<id>/reject/`         | admin    | Body: `{"reason": "..."}`. Records reviewer id.    |
| `GET  /api/v1/community-plugins/<id>/review-history/` | admin    | Upload and review timeline built from the plugin row's own timestamps. Not an append-only audit log. |

## Serializer discipline

Three serializers, one audience each:

- `to_dict`: public. Metadata only. **Never** includes `file_path`,
  `source_code`, reviewer identity, resource limits, or rejection
  reason.
- `to_owner_dict`: the uploader's own view. `to_dict` +
  `rejection_reason` + `user_id`.
- `to_admin_dict`: admin-only. `to_owner_dict` + reviewer id +
  reviewed timestamp + `execution_timeout` + `memory_limit`. Source
  code is still not in this dict; admins fetch it through the source
  endpoint, which reads the file server-side.

`file_path` is a server-side implementation detail and must not appear
in any API response. There are pytest assertions
(`TestSerializersNeverLeakFilePath`) that fail if it ever does.

## Upload validation

Uploads are checked in this order, and rejection at any step aborts the
whole request without writing a DB row or a file:

1. Extension is `.py`.
2. Body size is within `PLUGIN_UPLOAD_MAX_SIZE`.
3. Metadata (`name`, `description`, `group`, `type`, `author`) is
   well-formed and within length limits.
4. Name is unique in the DB.
5. AST validator (`owtf.plugin.validator.PluginValidator`) accepts the
   code. This is the primary safety gate: it rejects `import
   subprocess`, `os.system`, `exec`, `eval`, dynamic imports, and a
   handful of other obviously-dangerous patterns.

On success the plugin is written to disk under `COMMUNITY_PLUGINS_DIR`
with a randomised suffix, marked `pending`, and returned to the
uploader in `to_owner_dict` shape.

## What the sandbox does and does not protect against

The AST validator is a **static** check on plugin source. It catches
common patterns that would obviously escape the plugin runtime, but it
does not:

- run the code in a container or seccomp jail;
- limit filesystem or network access at the OS level;
- prevent a determined attacker from smuggling behaviour through
  metaprogramming (`__import__`, `getattr` chains, decoded strings);
- protect against side effects triggered at import time.

The marketplace assumes an **admin reviews the source** before
approval. Approval is the trust decision, and admins are expected to
read the code, not just click a button. Any additional runtime
sandboxing (containers, resource limits enforced by the OS) is
explicitly out of scope for this PR and belongs to a follow-up.

## Test-run isolation

`POST /<id>/test-run/` is admin-only, rate-limited to 3 calls per 60s
per admin, and does not persist output through the scan pipeline. It
uses the standard plugin runner so its behaviour matches production,
but the output is returned inline and thrown away. This is
deliberately not exposed to regular users: running an unreviewed
plugin bypasses the "admin reviews source before approval" guarantee.

## Upgrade behaviour

New installs get the schema from `Model.metadata.create_all` at
startup. Existing installs that already have a `user_plugins` table
from an earlier version of this branch pick up any new columns via
`owtf.db.upgrade.run_startup_upgrades`, which runs `ALTER TABLE ADD
COLUMN` for every column the model expects but the table does not
have. It is idempotent, safe to call on every boot, and does not touch
existing data.

## What is out of scope

- Rating and review UI for regular users.
- Plugin signing / verification of upload provenance.
- Runtime sandboxing beyond static AST validation.
- Multi-admin quorum for approval.

If a reviewer opens one of these threads on the current PR, the
answer is "later, tracked separately, not blocking this merge."
