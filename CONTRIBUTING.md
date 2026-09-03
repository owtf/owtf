# Contributing to OWTF

Thank you for considering a contribution to the OWASP Offensive Web Testing Framework (OWTF)! Whether you found a bug, want to
add a feature, or improve our documentation, every contribution makes OWTF better for the community.

## How to get involved

- **Ask questions** – Join the [OWASP Slack workspace](https://owasp.org/slack/invite) and head to `#project-owtf`.
- **Report issues** – Search the [issue tracker](https://github.com/owtf/owtf/issues) before opening a new ticket. Provide as
  much detail as possible (steps to reproduce, expected behaviour, environment details, and logs where relevant).
- **Contribute code or documentation** – Pick an open issue or propose a new improvement, then submit a pull request.

Please make sure you read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Development workflow

1. **Fork and clone** the repository, then create a feature branch:
   ```bash
   git clone https://github.com/<your-username>/owtf
   cd owtf
   git checkout -b feature/my-change
   ```
2. **Set up OWTF** with the Docker Compose instructions in the [README](README.md). For backend-only host development, use
   Python 3.11 or 3.12 in a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install -r requirements/base.txt -r requirements/dev.txt -r requirements/test.txt
   OWTF_SKIP_POST_INSTALL=1 python -m pip install -e . --no-deps
   make startdb
   ```
   Install frontend dependencies separately with `cd owtf/webapp && yarn install --frozen-lockfile`.
3. **Run the tests and linters** before submitting your changes:
   ```bash
   make startdb
   make lint
   pytest
   ```
   You can run specific test modules using `pytest tests/<path>::<TestClass>`.
4. **Keep commits focused**. Write clear commit messages in the present tense (e.g. `Fix crash in plugin loader`).
5. **Submit a pull request** to the `develop` branch. Describe what changed, why it matters, and include any testing steps.

## Style guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code unless the existing module uses a different convention.
- Use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting (`make lint-py` / `make format-py`) on the maintained runtime module set.
- Run static type checks with `make typecheck-py` (mypy targeted modules).
- Type hints are encouraged for new modules and functions.
- Update or add documentation and tests relevant to your change. New features should include at least one automated test where
  feasible.

## Pull request checklist

Before requesting a review, double-check that:

- [ ] Tests, linting, and type checks pass locally.
- [ ] New or updated documentation is included when needed.
- [ ] Any user-facing changes are described in the pull request summary.
- [ ] You have added yourself to `AUTHORS.md` if you are a new contributor.

## Reporting security issues

Please do **not** open a public issue if you find a security vulnerability. Instead, follow the steps outlined in our
[Security Policy](SECURITY.md).

## Recognition

We are grateful to everyone who contributes to OWTF. Project authors and contributors are listed in
[AUTHORS.md](AUTHORS.md).

Thank you for helping us build a stronger, more secure web!
