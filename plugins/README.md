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

Retained plugins without a finished executor use `runtime.type: unavailable`.
They stay visible with a concrete reason and known command requirements, but
group launches exclude them until a real runtime replaces that declaration.
