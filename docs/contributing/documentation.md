# Contribute to the documentation

The documentation is written in Markdown and built with MkDocs Material.

## Set up the docs environment

From the repository root:

```bash
python3 -m venv .venv-docs
source .venv-docs/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/docs.txt
```

## Preview locally

```bash
mkdocs serve
```

Open the local address printed by MkDocs. Changes reload automatically.

## Validate before submitting

```bash
mkdocs build --strict
```

Strict builds fail on broken internal links, missing navigation pages, invalid configuration, and other documentation warnings.

## Writing guidelines

- Start with the task the reader is trying to complete.
- Use the supported Docker Compose workflow for end-user installation.
- Distinguish the web interface (`8019`), backend API (`8009`), and proxy (`8008`).
- Mark commands that send traffic or delete data with an appropriate warning.
- Do not claim a feature works unless it is connected to the real execution path.
- Prefer current interface names over screenshots that become stale quickly.
- Never include real targets, credentials, tokens, or customer data.

## Add a page

1. Create a Markdown file under the closest section in `docs/`.
2. Add it to `nav` in `mkdocs.yml`.
3. Link it from a related page so readers can discover it in context.
4. Run a strict build.

For larger structural changes, explain the navigation and migration impact in the pull request.
