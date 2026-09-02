# OWTF documentation

The maintained design and operator documentation is intentionally small:

- `architecture/owtf-next.rst` defines the control-plane boundaries, plugin
  contract, task lifecycle, phase gates, and resource constraints.
- `architecture/legacy-plugin-inventory.csv` records the legacy technique
  codes and metadata used to decide which plugins to reimplement.
- `usage/owtf-next-cli.rst` documents the current CLI surface.
- `usage/access-model.rst` documents the deliberate absence of application
  authentication.

Go package documentation lives beside the code and is available with `go doc`.
Update package comments and exported-symbol comments in the same change as the
behavior they describe.
