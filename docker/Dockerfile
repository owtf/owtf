FROM kalilinux/kali-rolling:latest

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

# Install dependencies
RUN apt-get -y update && apt-get clean
RUN apt-get -y install  xvfb xserver-xephyr libxml2-dev libxslt-dev libssl-dev zlib1g-dev gcc python-all-dev \
postgresql-server-dev-all postgresql-client postgresql-client-common \
postgresql libcurl4-openssl-dev proxychains tor ca-certificates libpq-dev  \
libxslt1-dev libldap2-dev libsasl2-dev libffi-dev net-tools lsof locales-all 

RUN apt-get install -y --no-install-recommends make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

ENV HOME="/root"
WORKDIR ${HOME}
RUN apt-get install -y git
RUN git clone --depth=1 https://github.com/pyenv/pyenv.git .pyenv
ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"

ENV PYTHON_VERSION=3.9
RUN pyenv install ${PYTHON_VERSION}
RUN pyenv global ${PYTHON_VERSION}
RUN pyenv --version
RUN python --version


# Set locale
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install optional tools (LBD, arachni, gnutls-bin, o-saft and metagoofil) (not available on ubuntu20)
RUN apt-get -y install lbd theharvester tlssled nikto dnsrecon nmap whatweb skipfish dirbuster \
metasploit-framework wpscan wapiti hydra metagoofil o-saft amass 

# Create a dedicated OWTF directory to copy source to and run from.
RUN cd / && /bin/mkdir -p owtf
ADD . /owtf
ADD docker/wait-for-it.sh /usr/bin/wait-for-it.sh
RUN chmod +x /usr/bin/wait-for-it.sh

#Create and activating a python virtualenv
ENV VIRTUAL_ENV=/bin/owtf
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Ensure pip and setuptools are at their latest versions
RUN pip install --upgrade pip
RUN pip install setuptools==57.5.0
RUN pip install cffi
RUN pip install wheel

#Installing python dependencies
RUN pip install -r /owtf/requirements/base.txt

# Install OWTF using the recommended method (setup.py)
RUN cd /owtf &&\
python setup.py install

# Set the current working directory to OWTF root directory
WORKDIR /owtf

# Expose the required ports for OWTF to run
EXPOSE 8008 8009 8010
