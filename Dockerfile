FROM kalilinux/kali-linux-docker

MAINTAINER Viyat Bhalodia viyat.bhalodia@owasp.org

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
                        python-pip postgresql-server-dev-all postgresql-client postgresql-client-common \
                        postgresql libcurl4-openssl-dev proxychains tor ca-certificates libpq-dev python-dev \
                        libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libffi-dev

# Install optional tools (LBD, arachni, gnutls-bin, o-saft and metagoofil)
RUN apt-get -y install  lbd arachni theharvester tlssled nikto dnsrecon nmap whatweb skipfish dirbuster \
                        metasploit-framework wpscan wapiti hydra metagoofil o-saft

# Ensure pip and setuptools are at their latest versions
RUN pip install setuptools --upgrade
RUN pip install pip --upgrade
RUN pip install cffi

# Install and create a Python virtualenv
RUN pip install virtualenv && virtualenv ~/.venv/owtf && . ~/.venv/owtf/bin/activate

# Create a dedicated OWTF directory to copy source to and run from.
RUN cd / && /bin/mkdir -p owtf
ADD . /owtf

# Copy the configuration file intended for the Docker environment
RUN cp -f /owtf/docker/default.settings.py /owtf/owtf/settings.py

# Install OWTF using the recommended method (setup.py)
RUN cd /owtf &&\
  python setup.py develop

# Set the current working directory to OWTF root directory
WORKDIR /owtf

# Expose the required ports for OWTF to run
EXPOSE 8008 8009 8010




