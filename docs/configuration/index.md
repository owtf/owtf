# Configuration

The supported Compose setup ships with development defaults. Most users can start OWTF without editing configuration, but teams should understand where settings live before changing ports, credentials, proxy behavior, or plugin profiles.

## Configuration layers

| Layer | Location | Purpose |
| --- | --- | --- |
| Compose services | `docker/docker-compose.dev.yml` | Containers, port mappings, database environment, volumes, and service networking |
| Runtime settings | `owtf/settings.py` | Server, proxy, authentication, storage, and default application values |
| Local runtime overrides | `~/.owtf/settings.py` | Optional Python settings loaded after defaults |
| Framework configuration | `~/.owtf/conf/framework.yaml` | Tool choices and framework behavior copied during bootstrap |
| General configuration | `~/.owtf/conf/general.yaml` | Plugin and resource settings copied during bootstrap |

The `~/.owtf` path is inside the backend container when using Docker Compose unless you explicitly persist or map it.

## Prefer narrow overrides

Avoid editing `owtf/settings.py` for machine-specific values. For contributor workflows, place supported overrides in `~/.owtf/settings.py` or change the Compose environment and mounts in a local override file.

Example local settings file:

```python
# ~/.owtf/settings.py
DEBUG = False
APP_SECRET = "replace-with-a-random-secret"
```

Never commit real secrets.

## Profiles and plugin resources

OWTF copies default configuration from `owtf/data/conf/` into the runtime configuration directory. Plugin order, groups, resources, and tool choices are data-driven. Keep a reviewable copy of team-specific changes and recheck them after updating OWTF.

## Internet-facing deployments

The development Compose files are not a hardened production deployment and should not be exposed to an untrusted network. A production deployment needs a separate hardening review covering bind addresses, all application and JWT secrets, CORS origins, database credentials, TLS termination, authentication, log retention, and access to the intercepting proxy.
