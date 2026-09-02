# Contributing to OWTF

OWTF accepts focused changes that improve its use as an authorized security
testing harness. Discuss large changes in a GitHub issue or the OWASP Slack
`#project-owtf` channel before implementation.

## Development workflow

1. Install Go 1.24 or newer.
2. Create a focused branch from the current development branch.
3. Make the smallest coherent implementation and documentation change.
4. Run the complete local gate:

   ```bash
   make lint
   make test-next
   make test-next-api
   ```

5. Submit a pull request with the behavior changed, verification performed, and
   any compatibility impact.

The smoke flow is intentionally native and resource bounded. Do not require
Docker for unit or end-to-end development checks.

## Design rules

- Keep sessions, targets, plugin codes, worklist, workers, transactions, and
  reports as the operator-facing OWTF vocabulary.
- Keep orchestration in the Go control plane and durable state in SQLite.
- Run plugin commands as argument arrays. Do not interpolate target values into
  shell source.
- Declare plugin requirements and artifacts in `plugin.yaml`.
- Treat missing tools, malformed output, cancellation, and timeouts as explicit
  task states.
- Keep stdout and stderr as retained task events.
- Do not add application accounts, passwords, tokens, or a user database.
- Add package and exported-symbol documentation that explains ownership and
  invariants rather than restating names.
- Include tests that exercise the real storage, worklist, runner, and evidence
  path when behavior crosses those boundaries.

## Pull request checklist

- [ ] Formatting, static analysis, unit tests, and the curl/CLI smoke flow pass.
- [ ] New behavior has focused tests and operator-facing documentation.
- [ ] Plugin changes retain established OWTF technique codes where applicable.
- [ ] Error and cancellation states are visible rather than silently ignored.
- [ ] No secrets, credentials, or output artifacts are committed.

Report security issues through the process in [SECURITY.md](SECURITY.md), not a
public issue.
