# OWTF documentation

The maintained design and operator documentation is intentionally small:

- `architecture/overview.rst` defines the OWTF server boundaries, plugin
  contract, task lifecycle, phase gates, and resource constraints.
- `architecture/legacy-plugin-inventory.csv` records the legacy technique
  codes and metadata used to decide which plugins to reimplement.
- `architecture/feature-parity.csv` records implemented, partial, missing,
  replaced, removed, and deferred legacy outcomes.
- `architecture/settings-migration.md` summarizes the complete four-file legacy
  settings inventory; `settings-migration.csv` records each occurrence and gap.
- `architecture/settings-decisions.md` records verified differences, planned
  global controls, explicit retirements, and deferred plugin work.
- `usage/cli.rst` documents the current CLI surface.
- `usage/models.md` documents opt-in multi-provider model qualification.
- `architecture/ai.md` defines the AI boundary and subsequent increments.
- `usage/recovery.rst` covers Compose verification, backup/restore, and a manual CLI walkthrough.
- `usage/access-model.rst` documents the deliberate absence of application
  authentication.

Go package documentation lives beside the code and is available with `go doc`.
Update package comments and exported-symbol comments in the same change as the
behavior they describe.
