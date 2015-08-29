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

########### Pip is the foremost thing that must be installed along with some needed dependencies for python libraries
sudo -E apt-get install python-pip xvfb xserver-xephyr libxml2-dev libxslt-dev libcurl4-gnutls-dev libcurl4-nss-dev libcurl4-openssl-dev
export PYCURL_SSL_LIBRARY=gnutls # Needed for installation of pycurl using pip

############ Proposed clean solution instead of cloning by git
# Added Kali bleeding-edge repo as some tools which are frequently updated are in this repo
echo "[*] Adding Kali repos to install the missing tools"
sudo sh -c "echo 'deb http://http.kali.org/kali  kali main contrib non-free' >> /etc/apt/sources.list"
sudo sh -c "echo 'deb-src http://http.kali.org/kali kali main contrib non-free' >> /etc/apt/sources.list"
sudo sh -c "echo 'deb http://repo.kali.org/kali kali-bleeding-edge main contrib non-free' >> /etc/apt/sources.list"

sudo apt-get update
echo "[*] Done"
############ Tools missing in Samurai-WTF

############ Install updated w3af from GitHub
#mkdir -p $RootDir/tools/restricted
#cd $RootDir/tools/restricted
#IsInstalled "w3af"
#if [ $? -eq 0 ]; then # Not installed
#    git clone https://github.com/andresriancho/w3af.git
#fi

########## Remove default ruby-bundler to avoid with Metasploit later on
"$RootDir/install/samurai/samurai_wtf_patch_metasploit.sh" $RootDir

########## Installing missing tools
echo "[*] Installing missing tools"
sudo -E apt-get install lbd arachni tlssled set ua-tester wpscan theharvester whatweb dnsrecon metagoofil metasploit waffit

echo "[*] Installting Tor"
sudo -E apt-get install tor

########## Patch scripts
"$RootDir/install/kali/samurai_wtf_patch_w3af.sh"
"$RootDir/install/samurai/samurai_wtf_patch_nikto.sh"
"$RootDir/install/samurai/samurai_wtf_patch_tlssled.sh"

###### Dictionaries missing in Samurai-WTF
mkdir -p $RootDir/dictionaries/restricted
cd $RootDir/dictionaries/restricted
IsInstalled "dirbuster"
if [ $? -eq 0 ]; then # Not installed
    # Copying dirbuster dicts
    echo "\n[*] Copying Dirbuster dictionaries"
    mkdir -p dirbuster
    cp -r /usr/share/dirbuster/wordlists/. dirbuster/.
    echo "[*] Done"
else
    echo "WARNING: Dirbuster dictionaries are already installed, skipping"
fi
