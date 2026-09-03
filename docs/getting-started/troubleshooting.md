# Troubleshooting

Start with the container state and logs. Old fixes that install Python 2 packages or run the retired native installer do not apply to the supported Compose setup.

## The web interface does not open

Check whether the services are running:

```bash
docker compose -f docker/docker-compose.dev.yml ps
```

Then inspect recent logs:

```bash
docker compose -f docker/docker-compose.dev.yml logs --tail=200
```

The web interface is `http://localhost:8019`. Port `8009` is the backend API.

## A port is already in use

Identify the process or container already using `8019`, `8009`, `8008`, or PostgreSQL's mapped port. Stop the conflicting service or change the local Compose mapping before starting OWTF again.

## A service keeps restarting

Follow the affected service logs:

```bash
docker compose -f docker/docker-compose.dev.yml logs --follow SERVICE_NAME
```

Replace `SERVICE_NAME` with the name shown by `docker compose ... ps`. The first meaningful traceback or health-check failure is usually more useful than the final restart message.

## Rebuild after dependency changes

```bash
docker compose -f docker/docker-compose.dev.yml build --no-cache
make compose-safe
```

Use a no-cache build only when a normal rebuild still uses stale layers; it is slower and downloads more data.

## Reset local containers without deleting data

```bash
docker compose -f docker/docker-compose.dev.yml down
make compose-safe
```

Do not add `--volumes` unless you intentionally want to remove the local database and other persisted Compose data.

## Get help

When opening a [GitHub issue](https://github.com/owtf/owtf/issues), include:

- your operating system and architecture;
- Docker and Compose versions;
- the OWTF commit you are running;
- the failing service name;
- the smallest relevant log excerpt with credentials and target data removed; and
- exact reproduction steps.

For discussion, [join the OWASP Slack workspace](https://owasp.org/slack/invite) and use `#project-owtf`.
