# Get started

OWTF is a browser-based workspace for authorized web security assessments. The supported installation runs the application with Docker Compose so the Python service, web application, PostgreSQL database, and external tool dependencies stay isolated from your host system.

## The shortest path

1. [Install OWTF](installation.md) with Docker Compose.
2. Open the web interface at `http://localhost:8019`.
3. [Create your first assessment](first-assessment.md).
4. Use the [troubleshooting guide](troubleshooting.md) if the stack does not become healthy.

## What you need

- Git
- Docker Engine or Docker Desktop
- Docker Compose v2, available through the `docker compose` command
- Enough memory and disk space for the application images and security tools
- Explicit authorization for every target you test

No host-level Python or Node.js installation is required for the supported end-user path.

## Service addresses

| Service | Address | Purpose |
| --- | --- | --- |
| Web interface | `http://localhost:8019` | Use OWTF in a browser |
| Backend API | `http://localhost:8009` | Application API used by the web interface |
| Intercepting proxy | `localhost:8008` | Route authorized HTTP and HTTPS traffic through OWTF |

[See the complete port reference →](../reference/ports.md)
