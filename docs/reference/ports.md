# Service ports

The development Compose stack exposes these ports on the host:

| Port | Service | Open this in a browser? | Notes |
| ---: | --- | --- | --- |
| `8019` | Web interface | Yes | Primary OWTF user interface |
| `8009` | Backend API | Only for API calls | Base for `/api/v1/` endpoints |
| `8008` | Intercepting proxy | No | Configure as an HTTP proxy in an authorized test client |
| `8010` | File service | Normally no | Serves files used by reports and plugin output |
| `5432` | PostgreSQL | No | Development database exposed by the current Compose file |

## Bind-address warning

Published container ports may be reachable from more than the local machine depending on Docker and host firewall settings. Review the generated bindings before using OWTF on a shared or untrusted network:

```bash
docker compose -f docker/docker-compose.dev.yml ps
```

The checked-in Compose file is for development and authorized testing, not a hardened public deployment.
