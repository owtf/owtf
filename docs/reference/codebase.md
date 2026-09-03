# Codebase map

The old documentation generated hundreds of API entries from imports, including modules that no longer existed. This page gives contributors a maintained map of the current code instead.

| Path | Responsibility |
| --- | --- |
| `owtf/api/` | Tornado application, routes, request handlers, and API utilities |
| `owtf/db/` | Database session and startup upgrade support |
| `owtf/models/` | SQLAlchemy models |
| `owtf/managers/` | Application operations for targets, sessions, work, workers, plugins, results, and configuration |
| `owtf/plugin/` | Plugin discovery, parameters, execution, helpers, validation, and metrics |
| `owtf/plugins/` | Built-in web, network, auxiliary, and community plugin implementations |
| `owtf/proxy/` | Intercepting proxy, certificate generation, traffic handling, and interceptors |
| `owtf/requester/` | HTTP request support used by OWTF and plugins |
| `owtf/transactions/` | Transaction parsing and persistence support |
| `owtf/workers/` | Worker execution processes |
| `owtf/webapp/` | React web interface and frontend build configuration |
| `owtf/data/conf/` | Default framework, plugin, profile, and resource configuration |
| `docker/` | Backend/frontend images and development Compose stacks |
| `tests/` | Backend tests and test utilities |

## Trace an API change

For an API-backed feature, follow the complete path:

```text
frontend action
  └─► API route
       └─► request handler
            └─► manager
                 └─► model / worklist / plugin runner
```

Tests should cover the integration boundary, not only the helper function changed in isolation.

## Generate local Python API information

Use Python's built-in inspection tools or an IDE against the current checkout. OWTF's runtime modules can have environment and service dependencies, so importing the whole package merely to build documentation is intentionally avoided.

Source links in this site point to the `develop` branch. When documenting a tagged release, switch to the corresponding version of the docs.
