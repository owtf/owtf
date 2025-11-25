# Offensive Web Testing Framework (OWTF)

[![Build status](https://github.com/owtf/owtf/actions/workflows/main.yml/badge.svg)](https://github.com/owtf/owtf/actions/workflows/main.yml)
[![License: BSD 3-Clause](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg?style=flat-square)](LICENSE.md)
[![Python Versions](https://img.shields.io/badge/python-3.8%E2%80%933.11-blue.svg)](https://www.python.org/downloads/)

**OWASP OWTF** helps penetration testers stay efficient and aligned with security standards such as the OWASP Testing Guide (v3 and v4), the OWASP Top 10, PTES, and NIST so that they have more time to:

- See the big picture and think outside the box.
- Efficiently find, verify, and combine vulnerabilities.
- Investigate complex issues such as business logic flaws or multi-tenant edge cases.
- Perform targeted fuzzing on risky areas.
- Demonstrate meaningful impact despite tight assessment windows.

The tool is highly configurable, and anyone can create simple plugins or add new tests in configuration files without prior development experience.

> **Note**
> OWTF is not a silver bullet. Understanding and experience are still required to interpret tool output correctly and decide where to investigate further in order to demonstrate impact.

# Requirements

OWTF is developed on Kali Linux and macOS, and it is tailored for Kali Linux (or other Debian derivatives).

OWTF supports Python 3.

## macOS prerequisites

Install [Homebrew](https://brew.sh/) and then run:

```bash
python3 -m venv ~/.virtualenvs/owtf
source ~/.virtualenvs/owtf/bin/activate
brew install coreutils gnu-sed openssl
# Install 'cryptography' first to avoid issues
pip install cryptography --global-option=build_ext --global-option="-L/usr/local/opt/openssl/lib" --global-option="-I/usr/local/opt/openssl/include"
```

# Installation

## Running as a Docker container

Building the Docker image is the recommended way to use OWTF so you do not have to worry about dependency conflicts or installing a large toolchain manually.

- Install [`docker` and `docker-compose`](https://docs.docker.com/compose/install/).

```bash
git clone https://github.com/owtf/owtf
cd owtf
make compose-safe
```

## Installing directly

### Create and start the PostgreSQL database server

#### Using the preconfigured PostgreSQL Docker container (recommended)

> Make sure Docker is installed first.

Run `make startdb` to create and start the PostgreSQL server in a Docker container. In the default configuration it listens on port `5342`, exposed from the container.

#### Manual setup (painful and error-prone)

> You can also use a script to do this for you—see `scripts/db_setup.sh`. Modify any hardcoded variables if you change the corresponding values in `owtf/settings.py`.

Start the PostgreSQL server:

- macOS: `brew install postgresql` and `pg_ctl -D /usr/local/var/postgres start`
- Kali: `sudo systemctl enable postgresql; sudo systemctl start postgresql` (or `sudo service postgresql start`)

Create the `owtf_db_user` user:

- macOS: `psql postgres -c "CREATE USER $db_user WITH PASSWORD '$db_pass';"`
- Kali: `sudo su postgres -c "psql -c \"CREATE USER $db_user WITH PASSWORD '$db_pass'\""`

Create the database:

- macOS: `psql postgres -c "CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;"`
- Kali: `sudo su postgres -c "psql -c \"CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;\""`

### Installing OWTF

```bash
git clone https://github.com/owtf/owtf
cd owtf
python3 setup.py develop
make startdb
make setup-web
owtf
# Open http://localhost:8019 in your browser for the OWTF web interface, or run `owtf --help` for all available commands.
```

# Features

- **Resilience**: If one tool crashes, OWTF moves on to the next test and saves the partial output produced so far.
- **Flexible**: Pause and resume your work.
- **Test separation**: OWTF separates its traffic to the target into three plugin types:
  - **Passive** – No traffic is sent to the target.
  - **Semi passive** – Normal traffic to the target.
  - **Active** – Direct vulnerability probing.
- **Extensive REST API**.
- **Standards coverage**: Nearly complete OWASP Testing Guide (v3, v4), OWASP Top 10, NIST, and CWE coverage.
- **Web interface**: Manage large penetration engagements easily.
- **Interactive report**.
- **Automated plugin rankings** from tool output, fully configurable by the user.
- **Configurable risk rankings**.
- **Inline notes editor** for each plugin.

# License

Check out [LICENSE](LICENSE.md).

# Code of Conduct

Check out the [Code of Conduct](CODE_OF_CONDUCT.md).

# Links

- [Project homepage](http://owtf.github.io/)
- Legacy IRC (deprecated): [Freenode #owtf](http://webchat.freenode.net/?randomnick=1&channels=%23owtf&prompt=1&uio=MTE9MjM20f)
- [Wiki](https://www.owasp.org/index.php/OWASP_OWTF)
- **Primary**: [OWASP Slack](https://join.slack.com/t/owasp/shared_invite/enQtNDI5MzgxMDQ2MTAwLTEyNzIzYWQ2NDZiMGIwNmJhYzYxZDJiNTM0ZmZiZmJlY2EwZmMwYjAyNmJjNzQxNzMyMWY4OTk3ZTQ0MzFhMDY) – join `#project-owtf`
- Legacy mailing list (deprecated): [owasp_owtf_developers@lists.owasp.org](mailto:owasp_owtf_developers@lists.owasp.org)
- [User documentation](http://docs.owtf.org/en/latest/)
- [YouTube channel](https://www.youtube.com/user/owtfproject)
- [Slideshare](http://www.slideshare.net/abrahamaranguren/presentations)
- [Blog](http://blog.7-a.org/search/label/OWTF)
