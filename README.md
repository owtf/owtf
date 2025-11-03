# Offensive Web Testing Framework (OWTF)

[![Build status](https://github.com/owtf/owtf/actions/workflows/main.yml/badge.svg)](https://github.com/owtf/owtf/actions/workflows/main.yml)
[![License: BSD 3-Clause](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg?style=flat-square)](LICENSE.md)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%E2%80%93%203.11-blue.svg)](https://www.python.org/)

OWTF (the OWASP Offensive Web Testing Framework) is an OWASP flagship project focused on helping security testers align their
workflows with industry standards such as the OWASP Testing Guide, OWASP Top 10, PTES, and NIST.

The framework emphasises productivity: OWTF orchestrates tests, captures results even when tools fail, and lets you focus on
finding, validating, and clearly demonstrating real impact.

## Highlights

- **Resilient orchestration** – OWTF continues executions when tools fail and stores partial output for later review.
- **Flexible workflows** – pause and resume long-running test executions as needed.
- **Plugin-driven coverage** – Passive, Semi-Passive, and Active plugins give you fine-grained control of traffic sent to targets.
- **Rich reporting** – Manage engagements with a web UI, take inline notes, and configure risk ratings to suit your methodology.
- **REST API** – Automate or integrate OWTF into your existing pipelines.
- **Alignment with standards** – Almost complete coverage of OWASP Testing Guide v3/v4, OWASP Top 10, NIST, and CWE mappings.

## Table of contents

- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Manual installation](#manual-installation)
- [Usage](#usage)
- [Development](#development)
- [Support & community](#support--community)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Requirements

OWTF is developed and tested primarily on Kali Linux and macOS, but it is expected to work on other Debian-derived systems.

Core requirements include:

- Python 3.8 – 3.11
- PostgreSQL 12+
- Docker (optional, but recommended for quick start and database setup)

Additional third-party tools are invoked through OWTF plugins. The exact list depends on the tests you run.

## Quick start

The fastest way to try OWTF is by using Docker. You will need Docker Engine and Docker Compose installed.

```bash
# Clone the repository
git clone https://github.com/owtf/owtf
cd owtf

# Build the container image and start OWTF in a safe configuration
make compose-safe
```

After the services start, open <http://localhost:8019> to launch the OWTF interface. Use `Ctrl+C` to stop the stack, or run
`docker compose down` when you are done.

## Manual installation

Manual setup is helpful if you are developing OWTF or need tight integration with an existing toolchain.

### 1. Prepare a Python environment

```bash
python3 -m venv ~/.virtualenvs/owtf
source ~/.virtualenvs/owtf/bin/activate
pip install --upgrade pip
```

On macOS you may need additional packages: `brew install coreutils gnu-sed openssl`. Install the `cryptography` wheel first if you
encounter OpenSSL build errors:

```bash
pip install "cryptography>=41.0" --no-binary=:all: \
  --global-option=build_ext \
  --global-option="-L/usr/local/opt/openssl/lib" \
  --global-option="-I/usr/local/opt/openssl/include"
```

### 2. Start PostgreSQL

#### Using Docker (recommended)

```bash
make startdb
```

This command runs a preconfigured PostgreSQL instance listening on port `5342` inside a container.

#### Manual setup

If you prefer to install PostgreSQL yourself, ensure the credentials in `owtf/settings.py` match your local configuration.

```bash
# macOS
brew install postgresql
pg_ctl -D /usr/local/var/postgres start

# Kali / Debian
sudo systemctl enable postgresql
sudo systemctl start postgresql
# or: sudo service postgresql start
```

Create the database user and database referenced in `owtf/settings.py`:

```bash
psql postgres -c "CREATE USER $db_user WITH PASSWORD '$db_pass';"
psql postgres -c "CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;"
```

On Kali you can run the commands as the `postgres` user:

```bash
sudo -u postgres psql -c "CREATE USER $db_user WITH PASSWORD '$db_pass';"
sudo -u postgres psql -c "CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;"
```

### 3. Install OWTF

```bash
git clone https://github.com/owtf/owtf
cd owtf
pip install -r requirements/dev.txt  # or requirements/prod.txt for runtime environments
python3 setup.py develop
make setup-web
```

Start the services with:

```bash
make startdb  # skip if already running
owtf
```

Open <http://localhost:8019> for the web interface, or run `owtf --help` to explore CLI commands.

## Usage

- Launch a web assessment: `owtf --targets target_list.txt`.
- Pause or resume engagements through the web UI.
- Export reports and raw tool outputs for offline review.

Consult the [user documentation](http://docs.owtf.org/en/latest/) for advanced workflows, plugin configuration, and API usage.

## Development

We welcome pull requests! A minimal development loop usually involves:

```bash
make startdb
make lint
pytest
```

Check [`CONTRIBUTING.md`](CONTRIBUTING.md) for detailed guidelines, coding standards, and triage processes.

## Support & community

- [Project homepage](https://owasp.org/www-project-owtf/)
- [User documentation](http://docs.owtf.org/en/latest/)
- **Primary**: [OWASP Slack](https://join.slack.com/t/owasp/shared_invite/enQtNDI5MzgxMDQ2MTAwLTEyNzIzYWQ2NDZiMGIwNmJhYzYxZDJiNTM0ZmZiZmJlY2EwZmMwYjAyNmJjNzQxNzMyMWY4OTk3ZTQ0MzFhMDY) – join `#project-owtf` for the fastest response.
- [GitHub discussions](https://github.com/owtf/owtf/discussions)
- [Blog](http://blog.7-a.org/search/label/OWTF)
- [YouTube channel](https://www.youtube.com/user/owtfproject)
- Legacy (deprecated): [Project mailing list](mailto:owasp_owtf_developers@lists.owasp.org) and IRC on Freenode (`#owtf`). These channels are kept for archival purposes and are not actively monitored—please use Slack instead.

## Contributing

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for instructions on how to build, test, and submit changes. By participating you
agree to follow our [`Code of Conduct`](CODE_OF_CONDUCT.md).

## Security

If you discover a security vulnerability, please follow the steps described in [`SECURITY.md`](SECURITY.md).

## License

OWTF is released under the [BSD 3-Clause License](LICENSE.md).
