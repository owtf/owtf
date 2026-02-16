USER := $(shell whoami)
PROJ := owtf
PYTHON := python3
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
VENV_PATH := ${HOME}/.virtualenvs/${PROJ}
SHELL := /bin/bash
PY_QUALITY_PATHS := owtf/config.py owtf/lib/exceptions.py owtf/managers/config.py owtf/managers/target.py owtf/requester/base.py owtf/transactions/base.py owtf/transactions/main.py owtf/utils/http.py
DOCKER_COMPOSE_CMD := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; elif docker-compose --version >/dev/null 2>&1; then echo "docker-compose"; fi)

.PHONY: venv setup bootstrap web docs lint typecheck-py format-py clean bump build release local-up local-down local-status local-stop-app local-clean-ports
LOCAL_PORTS := 3000 8008 8009 8010

check-compose:
ifeq ($(strip $(DOCKER_COMPOSE_CMD)),)
	$(error Docker Compose not found. Install Docker Compose plugin (`docker compose`) or docker-compose)
endif

check-root:
ifeq ($(USER), root)
	@echo "WARNING: Installing as root should be avoided at all costs. Use a virtualenv."
endif

clean-pyc:
	-find . -type f -a \( -name "*.pyc" -o -name "*$$py.class" \) | xargs rm -rf
	-find . -type d -name "__pycache__" | xargs rm -rf

clean-build:
	rm -rf build/ dist/ .eggs/ *.egg-info/ .tox/ .coverage cover/

### INSTALL

install-dependencies:
	@echo "--> Installing Kali dependencies"
	sudo apt-get update
	sudo apt-get install -y python3 git
	sudo apt-get install -y xvfb xserver-xephyr libxml2-dev libxslt-dev libssl-dev zlib1g-dev gcc python-all-dev \
			python3-pip postgresql-server-dev-all postgresql-client postgresql-client-common postgresql  \
			libcurl4-openssl-dev proxychains tor libffi-dev golang-go

opt-tools:
	sudo apt-get install -y lbd gnutls-bin o-saft metagoofil lbd  \
	                        theharvester tlssled nikto dnsrecon nmap whatweb skipfish dirbuster metasploit-framework \
	                        wpscan wapiti  hydra metagoofil o-saft

venv:
	@echo "Installing the virtualenv for OWTF"
	rm -rf $(VENV_PATH)
	$(PYTHON) -m venv $(VENV_PATH) --clear


activate-virtualenv:
	chmod +x $(VENV_PATH)/bin/activate
	bash -c "$(VENV_PATH)/bin/activate"


setup: install-dependencies venv activate-virtualenv install-requirements


### REQUIREMENTS

install-python-requirements: check-root
	@echo "--> Installing Python development dependencies."
	pip3 install setuptools
	for f in `ls requirements/` ; do pip3 install -r requirements/$$f ; done

install-ui-requirements:
	@echo "--> Installing Node development dependencies."
	cd owtf/webapp && yarn

install-docs-requirements:
	@echo "--> Installing Sphinx dependencies"
	pip3 install sphinx sphinx_rtd_theme

install-requirements: install-python-requirements install-ui-requirements install-docs-requirements

web:
ifdef OWTF_ENV
	cd owtf/webapp && yarn run start
else
	@echo "--> No environment specified. Usage: make web OWTF_ENV={dev}"
endif

setup-web:
	@echo "--> Setting up the webapp on http://localhost:8019"
	cd scripts && ./setup_webapp.sh


post-install:
	@echo "--> Installing dictionaries and tools"
	python3 scripts/install_tools.py

bootstrap:
	@echo "--> Running explicit OWTF bootstrap steps"
	./scripts/install.sh

### DOCS

docs:
	@echo "--> Building docs"
	cd docs/ && make html

### DOCKER

docker-build:
	@echo "--> Building the docker image for develop"
	docker build -t owtf/owtf -f docker/Dockerfile.backend .

docker-run:
	@echo "--> Running the Docker development image"
	docker run -it -p 8009:8009 -p 8008:8008 -p 8010:8010 -v $(current_dir):/owtf owtf/owtf /bin/bash

### Options to allow docker to have permissive network capabilities, allowing it to run tools such as nmap
compose-safe: check-compose
	@echo "--> Running the Docker Compose setup with network capabilties for container"
	$(DOCKER_COMPOSE_CMD) -f docker/docker-compose.dev.yml up --build

compose-unsafe: check-compose
	@echo "--> Running the Docker Compose setup without network capabilties for container"
	$(DOCKER_COMPOSE_CMD) -f docker/docker-compose.dev.unsafe.yml up --build

### DEBIAN PACKAGING

build-debian:
	@echo "--> Building the Debian package"
	dpkg-buildpackage -us -uc -d

### LINT

lint-py:
	@echo "--> Linting Python files."
	python3 -m ruff check $(PY_QUALITY_PATHS)
	python3 -m ruff format --check $(PY_QUALITY_PATHS)

typecheck-py:
	@echo "--> Running targeted mypy checks."
	python3 -m mypy $(PY_QUALITY_PATHS)

format-py:
	@echo "--> Formatting Python files."
	python3 -m ruff format $(PY_QUALITY_PATHS)

lint-js:
	@echo "--> Linting JavaScript files."
	cd owtf/webapp && yarn lint

lint: lint-py lint-js

### TEST

test-py: clean-py
	@echo "--> Running Python tests (see test.log for output)."
	pytest | tee test.log  # settings in setup.cfg

test: test-py

tox: clean-py
	@echo "--> Running tox."
	tox "$@"

coverage-py: clean-py
	@echo "--> Running Python tests with coverage (see test.log and htmlcov/ for output)."
	pytest --cov-report html --cov=owtf | tee test.log  # settings in setup.cfg

### CLEAN

clean-py:
	@echo "--> Removing Python bytecode files."
	find . -name '__pycache__' -exec rm -rf {} \;  # Python 3
	find . -name '*.py[co]' -exec rm -rf {} \;  # Python 2

clean-js:
	@echo "--> Removing JavaScript build output."
	rm -rf owtf/webapp/build

clean-logs:
	@echo "--> Cleaning the logs and review folders"
	rm -rf owtf_review/ scans/

clean: clean-py clean-js clean-logs


### DISTCLEAN

distclean-py: clean-py
	@echo "--> Removing egg-info directory."
	rm -rf owtf.egg-info
	rm -rf build/
	rm -rf dist/

distclean-js:
	@echo "--> Removing node modules."
	rm -rf owtf/webapp/node_modules

distclean: distclean-py distclean-js

## MAINTAINERS
rollback:
	git reset --hard HEAD~1
	git tag -d `git describe --tags --abbrev=0`

bump:
	bumpversion patch && \
	echo -n "Now on version: " && \
	git describe --tags

bump-minor:
	bumpversion minor && \
	echo -n "Now on version: " && \
	git describe --tags

bump-major:
	bumpversion major && \
	echo -n "Now on version: " && \
	git describe --tags

release:
	python setup.py register sdist bdist_wheel upload

build:
	$(PYTHON) setup.py sdist bdist_wheel

startdb: check-compose
	$(DOCKER_COMPOSE_CMD) -p $(PROJ) -f docker/docker-compose.yml up -d

stopdb: check-compose
	$(DOCKER_COMPOSE_CMD) -p $(PROJ) -f docker/docker-compose.yml down

local-stop-app:
	@echo "--> Stopping local backend/frontend processes"
	@bash -lc '[ -f .run/owtf.pid ] && kill "$$(cat .run/owtf.pid)" 2>/dev/null || true; rm -f .run/owtf.pid'
	@bash -lc '[ -f .run/webapp.pid ] && kill "$$(cat .run/webapp.pid)" 2>/dev/null || true; rm -f .run/webapp.pid'

local-clean-ports:
	@echo "--> Releasing local ports: $(LOCAL_PORTS)"
	@bash -lc 'for p in $(LOCAL_PORTS); do pids=$$(lsof -ti tcp:$$p -sTCP:LISTEN 2>/dev/null || true); if [ -n "$$pids" ]; then echo "    killing :$$p -> $$pids"; kill $$pids 2>/dev/null || true; fi; done'
	@bash -lc 'sleep 1'

local-up: local-stop-app local-clean-ports startdb
	@echo "--> Starting OWTF backend + Vite frontend in background"
	@[ -x "$(VENV_PATH)/bin/owtf" ] || (echo "Missing $(VENV_PATH)/bin/owtf. Run: /opt/homebrew/bin/python3.11 -m venv $(VENV_PATH) && source $(VENV_PATH)/bin/activate && pip install -e ." && exit 1)
	@mkdir -p .run
	@bash -lc "source $(VENV_PATH)/bin/activate && nohup owtf > .run/owtf.log 2>&1 & echo \$$! > .run/owtf.pid"
	@nohup yarn --cwd owtf/webapp start > .run/webapp.log 2>&1 & echo $$! > .run/webapp.pid
	@echo "--> Ready:"
	@echo "    UI:      http://localhost:3000"
	@echo "    API:     http://localhost:8009"
	@echo "    Health:  http://localhost:8009/debug/health/"
	@echo "--> Logs:"
	@echo "    tail -f .run/owtf.log"
	@echo "    tail -f .run/webapp.log"

local-down: stopdb local-stop-app

local-status:
	@echo "--> Process status"
	@bash -lc '[ -f .run/owtf.pid ] && ps -p "$$(cat .run/owtf.pid)" >/dev/null 2>&1 && echo "backend: running (pid $$(cat .run/owtf.pid))" || echo "backend: stopped"'
	@bash -lc '[ -f .run/webapp.pid ] && ps -p "$$(cat .run/webapp.pid)" >/dev/null 2>&1 && echo "frontend: running (pid $$(cat .run/webapp.pid))" || echo "frontend: stopped"'
	@echo "--> DB status"
	@$(DOCKER_COMPOSE_CMD) -p $(PROJ) -f docker/docker-compose.yml ps 2>/dev/null || true
