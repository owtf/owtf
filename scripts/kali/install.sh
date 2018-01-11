#!/usr/bin/env sh

IsInstalled() {
	directory=$1
	if [ -d ${directory} ]; then
		return 1
	else
		return 0
	fi
}

RootDir=$1

"$RootDir/install/kali/kali_patch_w3af.sh"
"$RootDir/install/kali/kali_patch_nikto.sh"
"$RootDir/install/kali/kali_patch_tlssled.sh"

###### Dictionaries missing in Kali
mkdir -p ~/.owtf/dictionaries/restricted
cd ~/.owtf/dictionaries/restricted
IsInstalled "dirbuster"
if [ $? -eq 0 ]; then # Not installed
    # Copying dirbuster dicts
    echo "\n[*] Copying Dirbuster dictionaries"
    mkdir -p dirbuster
    cp -r /usr/share/dirbuster/wordlists/. dirbuster/.
    echo "[*] Done!"
else
    echo "[!] Dirbuster dictionaries are already installed, skipping"
fi
