# OWTF plugins

Plugins are grouped by the established OWTF plugin groups:

- `web`: web testing techniques.
- `network`: network service techniques.
- `auxiliary`: supporting tools that do not belong to a target test group.
- `community`: optional community-maintained plugins.

Each manifest lives at `<group>/<code>/<type>/plugin.yaml`. For example,
`web/OWTF-IG-004/grep/plugin.yaml` declares `OWTF-IG-004-grep`.

The manifest is the runtime source of truth. The directory layout keeps the
catalog navigable and is validated by the plugin tests.

`runtime.type: unavailable` is a temporary development state, not a shipped
replacement. No current manifest uses it. Optional external tools instead use
real command runtimes and report `missing_requirements` when not installed.
