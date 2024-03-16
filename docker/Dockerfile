# Stage 1: Base
FROM kalilinux/kali-rolling:latest AS base

LABEL Viyat Bhalodia viyat.bhalodia@owasp.org

# Bypass confirmations
ENV DEBIAN_FRONTEND noninteractive

# Fix for exporting a SHELL variable in the environment
ENV TERM xterm
ENV SHELL /bin/bash

# Flush the buffer for stderr, stdout logging
ENV PYTHONUNBUFFERED 1
# Python won’t try to write .pyc or .pyo files on the import of source modules
ENV PYTHONDONTWRITEBYTECODE 1

# Needed for installation of pycurl using pip in kali
ENV PYCURL_SSL_LIBRARY openssl

# Install dependencies and clean up in the same layer to reduce image size
RUN apt-get -y update && \
    apt-get -y install --no-install-recommends git xvfb xserver-xephyr libxml2-dev libxslt-dev libssl-dev zlib1g-dev gcc python-all-dev \
    postgresql-server-dev-all postgresql-client postgresql-client-common \
    postgresql libcurl4-openssl-dev proxychains tor ca-certificates libpq-dev  \
    libxslt1-dev libldap2-dev libsasl2-dev libffi-dev net-tools lsof locales-all \
    make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    lbd theharvester tlssled nikto dnsrecon nmap whatweb skipfish dirbuster metasploit-framework wpscan wapiti hydra metagoofil o-saft amass && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Stage 2: User Setup
FROM base AS owtf_setup

# Create a new user 'owtf' and switch to it
RUN useradd -ms /bin/bash owtf

ENV HOME="/home/owtf"
WORKDIR ${HOME}
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

ENV PYTHON_VERSION=3.9
RUN pyenv install ${PYTHON_VERSION}
RUN pyenv global ${PYTHON_VERSION}

# Set locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Create a dedicated OWTF directory to copy source to and run from.
ADD . ${HOME}
ADD docker/wait-for-it.sh /usr/bin/wait-for-it.sh
RUN chmod +x /usr/bin/wait-for-it.sh

USER owtf

#Create and activating a python virtualenv
ENV VIRTUAL_ENV="${HOME}/owtf-venv"
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Ensure pip and setuptools are at their latest versions
RUN pip install --upgrade pip
RUN pip install setuptools==57.5.0 cffi wheel

#Installing python dependencies
RUN pip install -r ${HOME}/requirements/base.txt

# Stage 3: Tool Installation
FROM owtf_setup AS final_install

USER root
RUN chown -R owtf:owtf ${HOME}
USER owtf

# Install OWTF using the recommended method (setup.py)
RUN cd ${HOME} &&\
python setup.py install

# Set the current working directory to OWTF root directory
WORKDIR ${HOME}

# Expose the required ports for OWTF to run
EXPOSE 8008 8009 8010
