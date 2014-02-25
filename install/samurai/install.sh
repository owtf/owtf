#!/usr/bin/env sh
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright 
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of the copyright owner nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
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
sudo -E apt-get install python-pip xvfb xserver-xephyr libxml2-dev libxslt-dev
export PYCURL_SSL_LIBRARY=gnutls # Needed for installation of pycurl using pip

############ Add custom ppa for some of the tools missing from Samurai-WTF
############ Kali-Proposed clean solution instead of cloning from Git
sudo echo deb http://ppa.launchpad.net/wagungs/kali-linux2/ubuntu precise main >> /etc/apt/sources.list
sudo echo deb-src http://ppa.launchpad.net/wagungs/kali-linux2/ubuntu precise main >> /etc/apt/sources.list
sudo echo deb http://ppa.launchpad.net/wagungs/kali-linux/ubuntu precise main >> /etc/apt/sources.list
sudo echo deb-src http://ppa.launchpad.net/wagungs/kali-linux/ubuntu precise main >> /etc/apt/sources.list

sudo apt-get update
sudo apt-get upgrade

############ Tools missing in Samurai-WTF
echo "[*] Installing LBD and arachni from custom Ubuntu PPAs"
sudo -E apt-get install lbd arachni tlssled openvas

########## Patch scripts
"$RootDir/install/samurai/samurai_wtf_patch_nikto.sh"
"$RootDir/install/samurai/samurai_wtf_patch_tlssled.sh"
"$RootDir/install/samurai/samurai_wtf_patch_openvas.sh" $RootDir

###### Dictionaries missing in Samurai-WTF
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