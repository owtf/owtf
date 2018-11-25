FROM kalilinux/kali-linux-docker

MAINTAINER @viyatb viyat.bhalodia@owasp.org

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && apt-get -y dist-upgrade && apt-get clean

RUN apt-get -y install build-essential libssl-dev libffi-dev python-dev
RUN apt-get -y install  xvfb \
                        xserver-xephyr \
                        libxml2-dev \
                        libxslt-dev \
                        libssl-dev \
                        zlib1g-dev \
                        gcc \
                        python-all-dev \
                        python-pip \
                        postgresql-server-dev-all \
                        postgresql-client \
                        postgresql-client-common \
                        postgresql  \
                        libcurl4-openssl-dev \
                        proxychains \
                        tor

# Needed for installation of pycurl using pip in kali
ENV PYCURL_SSL_LIBRARY openssl

# Install optional tools (LBD, arachni, gnutls-bin, o-saft and metagoofil)
RUN apt-get -y install  lbd \
                        arachni \
                        theharvester \
                        tlssled \
                        nikto \
                        dnsrecon \
                        nmap \
                        whatweb \
                        skipfish \
                        dirbuster \
                        metasploit-framework \
                        wpscan \
                        wapiti \
                        hydra \
                        metagoofil \
                        o-saft

# Fix for exporting a SHELL variable in the environment
ENV TERM xterm
ENV SHELL /bin/bash

# Install and create a Python virtualenv
RUN pip install virtualenv && virtualenv env/ && . env/bin/activate

ADD . /owtf
