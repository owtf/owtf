#!/usr/bin/env sh

IsInstalled() {
        directory=$1
        if [ -d $directory ]; then
                return 1
        else
                return 0
        fi
}

RootDir=$1

# Install headers for x86_64-linux-gnu-gcc
sudo -E apt-get install python-dev libpython-dev libffi-dev
# Grab and install pip
echo "[*] Installing pip using get-pip.py"
wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
sudo -H python get-pip.py
# Install dependancies
sudo -E apt-get install xvfb xserver-xephyr libxml2-dev libxslt-dev libcurl4-gnutls-dev libcurl4-nss-dev libcurl4-openssl-dev
export PYCURL_SSL_LIBRARY=gnutls

sudo -E apt-get install postgresql-server-dev-all

sudo -E apt-get install libcurl4-openssl-dev

echo "[*] Adding Kali Public Key for repos"
gpg --keyserver pgpkeys.mit.edu --recv-key ED444FF07D8D0BF6
echo "[*] Adding Kali repos to install the missing tools"

sudo sh -c "echo 'deb http://http.kali.org/kali  kali main contrib non-free' >> /etc/apt/sources.list"
sudo sh -c "echo 'deb-src http://http.kali.org/kali kali main contrib non-free' >> /etc/apt/sources.list"
sudo sh -c "echo 'deb http://repo.kali.org/kali kali-bleeding-edge main contrib non-free' >> /etc/apt/sources.list"

sudo apt-get update
echo "[*] Done"

echo "[*] Installing missing tools"
sudo -E apt-get install lbd arachni tlssled set ua-tester wpscan theharvester whatweb dnsrecon metagoofil metasploit waffit

echo "[*] Installting Tor"
sudo -E apt-get install tor

echo "[*] Cleaning up get-pip script"
rm *get-pip*


