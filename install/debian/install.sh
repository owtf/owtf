#!/usr/bin/env sh

# bring in the variables: `normal`, `info`, `warning`, `danger`, `reset`, `user_agent`
. "$(dirname "$(readlink -f "$0")")/../utils.sh"

IsInstalled() {
  directory=$1
  if [ -d ${directory} ]; then
    return 1
  else
    return 0
  fi
}

RootDir=$1

########### Pip is the foremost thing that must be installed along with some needed dependencies for python libraries

apt_wrapper_path="$RootDir/install/aptitude-wrapper.sh"

# Perform apt-get update before starting to install all packages, so we can get the latests manifests and packages versions
sudo apt-get update

# Grab and install pip
echo "${info}[*] Installing pip using get-pip.py${reset}"
wget --user-agent="${user_agent}" --tries=3 https://raw.github.com/pypa/pip/master/contrib/get-pip.py
sudo -E python get-pip.py

# Install headers for x86_64-linux-gnu-gcc
sudo -E "$apt_wrapper_path" install python-dev libpython-dev libffi-dev

# Install dependancies
sudo -E "$apt_wrapper_path" install xvfb xserver-xephyr libxml2-dev libxslt-dev libcurl4-gnutls-dev \
                                    libcurl4-nss-dev libcurl4-openssl-dev tor


# psycopg2 dependency
sudo -E "$apt_wrapper_path" postgresql-server-dev-all postgresql-client postgresql-client-common

# pycurl dependency
export PYCURL_SSL_LIBRARY=gnutls

echo "${normal}[*] Adding Kali Public Key for repos${reset}"
gpg --keyserver pgpkeys.mit.edu --recv-key ED444FF07D8D0BF6
echo "${normal}[*] Adding Kali repos to install the missing tools${reset}"

sudo sh -c "echo 'deb http://http.kali.org/kali  kali main contrib non-free' >> /etc/apt/sources.list"
sudo sh -c "echo 'deb-src http://http.kali.org/kali kali main contrib non-free' >> /etc/apt/sources.list"
sudo sh -c "echo 'deb http://repo.kali.org/kali kali-bleeding-edge main contrib non-free' >> /etc/apt/sources.list"

# Patch script for debian apt
echo "${normal}[*] Adding apt preferences in order to keep Debian free from Kali garbage as much as possible :P${reset}"
sh "$RootDir/install/debian/pref.sh"

sudo "$apt_wrapper_path" update

echo "${normal}[*] Installing missing tools${reset}"
sudo -E "$apt_wrapper_path" install lbd arachni tlssled nmap nikto skipfish w3af-console dirbuster wapiti hydra waffit \
                                    ua-tester wpscan theharvester whatweb dnsrecon metagoofil metasploit-framework o-saft

echo "${normal}[*] Cleaning up get-pip script${reset}"
rm *get-pip*

echo "${normal}[*] All done!${reset}"
