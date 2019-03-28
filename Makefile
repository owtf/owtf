USER := $(shell whoami)
PROJ=owtf
PYTHON=python3
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))
VENV_PATH=$$HOME/.virtualenvs/${PROJ}

.PHONY: venv setup web docs lint clean bump build release

check-root:
ifeq ($(USER), root)
	@echo "WARNING: Installing as root should be avoided at all costs. Use a virtualenv."
endif

clean-pyc:
	-find . -type f -a \( -name "*.pyc" -o -name "*$$py.class" \) | xargs rm
	-find . -type d -name "__pycache__" | xargs rm -r

clean-build:
	rm -rf build/ dist/ .eggs/ *.egg-info/ .tox/ .coverage cover/

### INSTALL

install-dependencies:
	@echo "--> Installing Kali dependencies"
	sudo apt-get update
	sudo apt-get install -y python git
	sudo apt-get install -y xvfb xserver-xephyr libxml2-dev libxslt-dev libssl-dev zlib1g-dev gcc python-all-dev \
			python-pip postgresql-server-dev-all postgresql-client postgresql-client-common postgresql  \
			libcurl4-openssl-dev proxychains tor libffi-dev

opt-tools:
	sudo apt-get install -y lbd gnutls-bin arachni o-saft metagoofil lbd arachni \
	                        theharvester tlssled nikto dnsrecon nmap whatweb skipfish dirbuster metasploit-framework \
	                        wpscan wapiti waffit hydra metagoofil o-saft

venv:
	@echo "Installing the virtualenv for OWTF"
	rm -rf $(VENV_PATH)
	$(PYTHON) -m venv $(VENV_PATH) --clear

web-tools:
	sudo apt-get install kali-linux-web

activate-virtualenv:
	source $(VENV_PATH)/bin/activate


setup:  venv activate-virtualenv install-requirements


### REQUIREMENTS

install-python-requirements: setup.py check-root
	@echo "--> Installing Python development dependencies."
	pip install setuptools
	for f in `ls requirements/` ; do pip install -r requirements/$$f ; done

install-ui-requirements:
	@echo "--> Installing Node development dependencies."
	cd owtf/webapp && yarn

install-docs-requirements:
	@echo "--> Installing Sphinx dependencies"
	pip install sphinx sphinx_rtd_theme

install-requirements: install-python-requirements install-ui-requirements install-docs-requirements

web:
ifdef OWTF_ENV
	cd owtf/webapp && yarn run ${OWTF_ENV}
else
	@echo "--> No environment specified. Usage: make OWTF_ENV={dev, prod} web"
endif

post-install:
	@echo "--> Installing dictionaries and tools"
	python scripts/install_tools.py

### DOCS

docs:
	@echo "--> Building docs"
	cd docs/ && make html

### DOCKER

docker-build:
	@echo "--> Building the docker image for develop"
	docker build -t owtf/owtf -f docker/Dockerfile .

docker-run:
	@echo "--> Running the Docker development image"
	docker run -it -p 8009:8009 -p 8008:8008 -p 8010:8010 -v $(current_dir):/owtf owtf/owtf /bin/bash

compose:
	@echo "--> Running the Docker Compose setup"
	docker-compose -f docker/docker-compose.dev.yml up

### DEBIAN PACKAGING

build-debian:
	@echo "--> Building the Debian package"
	dpkg-buildpackage -us -uc -d

### LINT

lint-py:
	@echo "--> Linting Python files."
	pep8 owtf tests  # settings in setup.cfg

lint-js:
	@echo "--> Linting JavaScript files."
	cd owtf/webapp && yarn lint

lint: lint-py lint-js

### TEST

test-py: clean-py
	@echo "--> Running Python tests (see test.log for output)."
	py.test | tee test.log  # settings in pytest.ini

test: test-py

tox: clean-py
	@echo "--> Running tox."
	tox "$@"

coverage-py: clean-py
	@echo "--> Running Python tests with coverage (see test.log and htmlcov/ for output)."
	py.test --cov-report html --cov=owtf | tee test.log  # settings in pytest.ini

### CLEAN

clean-py:
	@echo "--> Removing Python bytecode files."
	find . -name '__pycache__' -delete  # Python 3
	find . -name '*.py[co]' -delete  # Python 2

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

bump:
	bumpversion patch

bump-minor:
	bumpversion minor

bump-major:
	bumpversion major

release:
	python setup.py register sdist bdist_wheel upload

build:
	$(PYTHON) setup.py sdist bdist_wheel

startdb:
	docker-compose -p $(PROJ) -f docker/docker-compose.yml up -d --no-recreate

stopdb:
	docker-compose -p $(PROJ) -f docker/docker-compose.yml down
