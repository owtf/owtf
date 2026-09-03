# Architecture

OWTF separates the browser interface, API, work scheduling, plugin execution, proxy, and persistence layers. Docker Compose connects those pieces for local development and testing.

## Runtime view

```text
┌────────────────────┐       ┌─────────────────────────┐
│ Web interface      │       │ Backend API             │
│ React · :8019      │──────►│ Tornado · :8009         │
└────────────────────┘       └───────────┬─────────────┘
                                        │
                         ┌──────────────┼──────────────┐
                         │              │              │
                         ▼              ▼              ▼
                  PostgreSQL       worklist        file service
                    :5432          + workers          :8010
                                        │
                                        ▼
                                  plugins + tools

authorized client ───────────────► intercepting proxy :8008 ──► target
```

## Web interface

The React application presents target management, plugin launchers, worker and worklist controls, reports, authentication, and proxy tooling. It calls the backend API rather than accessing PostgreSQL directly.

## Backend API

The Tornado application defines versioned routes under `/api/v1/`. Handlers validate requests and delegate application work to managers and model operations.

## Managers and models

Managers implement operations over sessions, targets, plugins, results, workers, transactions, and the worklist. SQLAlchemy models define persisted state in PostgreSQL.

## Scheduler, worklist, and workers

A plugin launch creates work for a target. The worklist stores pending items, the scheduler decides which eligible item should run next, and workers execute plugins. Results and status changes flow back through the backend for the web interface to display.

## Plugin system

Plugins combine Python orchestration with data-driven profiles and resources. They may invoke external security tools installed in the backend image. Plugin type and group affect discovery, presentation, and scheduling.

## Intercepting proxy

The proxy accepts client traffic on port `8008`, records transactions, and supports HTTPS interception with a local certificate authority. Captured traffic becomes available to reports and proxy analysis tools.

## Persistence and files

PostgreSQL stores structured application state. Plugin-generated files and logs live in configured output paths and are exposed through the file service when needed by the web interface.
