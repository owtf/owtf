# Targets and sessions

Targets define the systems in scope. Sessions keep targets, queued work, and results organized by engagement or testing context.

## Add targets

Open the target manager and enter one URL per line. Include the scheme:

```text
https://shop.example.test
https://api.example.test
```

Use hostnames and paths exactly as approved in the rules of engagement. Treat a redirect to a different host as a new scope decision, not automatic permission.

## Review the target table

The target table is the main place to:

- search and filter targets;
- select one or more targets for plugin launches;
- open an individual target report;
- compare analyst rankings; and
- export the current target list.

Launching a plugin for several selected targets creates separate work for every plugin-target pair.

## Use sessions to separate work

A target can appear in more than one session. Use sessions to keep engagements or testing phases distinct—for example, a baseline assessment and a later retest.

Before switching sessions, confirm that the active session matches the scope you intend to change. New targets and plugin launches apply to the active session.

## Remove a target carefully

Removing a target can affect access to its queued work and collected results. Export any evidence you need to retain and confirm the target is no longer required before deleting it.

## Practical naming

Prefer names that are recognizable without containing credentials or confidential findings:

```text
customer-portal-staging-2026-q3
api-retest-2026-09
```
