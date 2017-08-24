#!/usr/bin/env sh

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`
. "$(dirname "$(readlink -f "$0")")/../utils/utils.sh"

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

apt_wrapper_path="$RootDir/install/utils/aptitude-wrapper.sh"
# Perform apt-get update before starting to install all packages, so we can get the latests manifests and packages versions
sudo apt-get update

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
