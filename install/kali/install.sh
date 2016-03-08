#!/usr/bin/env sh

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`
. "$(dirname "$(readlink -f "$0")")/../colors.sh"

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
sudo -E "$apt_wrapper_path" python-pip xvfb xserver-xephyr libxml2-dev libxslt-dev
export PYCURL_SSL_LIBRARY=gnutls # Needed for installation of pycurl using pip in kali

# psycopg2 dependency
sudo -E "$apt_wrapper_path" postgresql-server-dev-all postgresql-client postgresql-client-common

# pycurl dependency
sudo -E "$apt_wrapper_path" libcurl4-openssl-dev

############ Tools missing in Kali
#mkdir -p $RootDir/tools/restricted
#cd $RootDir/tools/restricted
#IsInstalled "w3af"
#if [ $? -eq 0 ]; then # Not installed
#    git clone https://github.com/andresriancho/w3af.git
#fi

echo "${info}[*] Installing LBD, arachni, gnutls-bin and metagoofil from Kali Repos${reset}"
sudo -E "$apt_wrapper_path" lbd gnutls-bin arachni metagoofil

echo "${info}[*] Installing ProxyChains${reset}"
sudo -E "$apt_wrapper_path" proxychains

echo "${info}[*] Installing Tor${reset}"
sudo -E "$apt_wrapper_path" tor

########## Patch scripts
sh "$RootDir/install/kali/kali_patch_w3af.sh"
sh "$RootDir/install/kali/kali_patch_nikto.sh"
sh "$RootDir/install/kali/kali_patch_tlssled.sh"
###### Dictionaries missing in Kali
mkdir -p ${RootDir}/dictionaries/restricted
cd ${RootDir}/dictionaries/restricted
IsInstalled "dirbuster"
if [ $? -eq 0 ]; then # Not installed
    # Copying dirbuster dicts
    echo "${info}\n[*] Copying Dirbuster dictionaries${info}"
    mkdir -p dirbuster
    cp -r /usr/share/dirbuster/wordlists/. dirbuster/.
    echo "${normal}[*] Done!${reset}"
else
    echo "${warning}[!] Dirbuster dictionaries are already installed, skipping${reset}"
fi
