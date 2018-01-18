USER := $(shell whoami)
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(notdir $(patsubst %/,%,$(dir $(mkfile_path))))

check-root:
ifeq ($(USER), root)
	@echo "WARNING: Installing as root should be avoided at all costs. Use a virtualenv."
endif


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
                        theharvester tlssled nikto dnsrecon nmap whatweb skipfish \
                        dirbuster metasploit-framework wpscan wapiti waffit hydra metagoofil o-saft

web-tools:
	sudo apt-get install kali-linux-web

activate-virtualenv:
	pip install virtualenv
	virtualenv ${HOME}/.venv/owtf
	source "${HOME}/.venv/owtf/bin/activate"

### REQUIREMENTS

install-python-requirements: setup.py check-root
	@echo "--> Installing Python development dependencies."
	pip install setuptools
	pip install -r requirements.txt

install-ui-requirements:
	@echo "--> Installing Node development dependencies."
	cd owtf/webapp && yarn

install-docs-requirements:
	@echo "--> Installing Sphinx dependencies"

install-requirements: install-python-requirements install-node-requirements

react-build:
	cd owtf/webapp && yarn build

develop: install-requirements react-build

build-ui: install-ui-requirements react-build

develop-ui:
	cd owtf/webapp && yarn run

install-develop-ui: install-node-requirements develop-ui

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
	docker build -t owtf/owtf -f Dockerfile.dev .

docker-run:
	@echo "--> Running the Docker development image"
	docker run -it -p 8009:8009 -p 8008:8008 -p 8010:8010 -v $(current_dir):/owtf owtf/owtf /bin/bash

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

