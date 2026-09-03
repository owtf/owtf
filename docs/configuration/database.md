# Database configuration

OWTF stores sessions, targets, queued work, plugin output metadata, and authentication data in PostgreSQL.

## Docker Compose

The supported local setup starts PostgreSQL as the `db` service and passes these environment variables to the backend:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

Inside the Compose network, the backend connects to host `db` on port `5432`.

The checked-in Compose credentials are development defaults. Do not reuse them for an environment exposed to other users or networks.

## Native contributor setup

Outside Docker, runtime settings default to a PostgreSQL server on `127.0.0.1:5432`. Override connection values in `~/.owtf/settings.py` or use the supported environment setting for the PostgreSQL host.

```python
# ~/.owtf/settings.py
DATABASE_IP = "127.0.0.1"
DATABASE_PORT = 5432
DATABASE_NAME = "owtf_db"
DATABASE_USER = "owtf_db_user"
DATABASE_PASS = "use-a-secret-manager-or-local-secret"
```

## Protect assessment data

The database can contain target details, user accounts, execution history, and references to sensitive evidence. Restrict database access, encrypt backups, and apply the engagement's retention policy.

Do not remove Compose volumes while you still need the stored assessment state.
