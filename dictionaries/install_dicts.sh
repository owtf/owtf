#!/usr/bin/env bash
#
# Description: Installation script for dictionaries with licensing issues.
#
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

DecompressTBZ2() {
	bunzip2 *
	tar xvf *
	rm -f *.tar 2> /dev/null
}

DecompressTGZ() {
	tar xvfz *
	rm -f *.tar.gz 2> /dev/null
	rm -f *.tgz 2> /dev/null
}

DecompressZIP() {
	unzip *.zip
	rm -f *.zip
}

Chmod700() {
	chmod 700 *
}

WgetInstall() {
	download_url=$1
	directory=$2
	decompress_method="tar.gz"
	if [ $3 ]; then
		decompress_method=$3
	fi

	IsInstalled "$directory"
	if [ $? -eq 0 ]; then # Not installed
		mkdir -p $directory
		(
			cd $directory
			echo "$directory not found, downloading it.."
			wget -A "MSIE 6.0" $download_url
			if [ "$decompress_method" = "tar.gz" ]; then
				DecompressTGZ
			elif [ "$decompress_method" = "tar.bz2" ]; then
				DecompressTBZ2
			elif [ "$decompress_method" = "zip" ]; then
				DecompressZIP
			elif [ "$decompress_method" = "chmod700" ]; then
				Chmod700
			fi
		)
	else
		echo "WARNING : $directory ($download_url) is already installed, skipping"
	fi
}

# This script needs to be run to download dictionaries with potentially restrictive licensing (cannot be redistributed)
DICTS_DIRECTORY="$(dirname $0)"
INSTALL_DIR="$DICTS_DIRECTORY/restricted"
mkdir -p $INSTALL_DIR
(
    # Copying raft dicts from shipped files in OWTF
    echo "[*] Copying RAFT dictionaries"
    mkdir -p $INSTALL_DIR/raft
    for file in $(ls $DICTS_DIRECTORY/fuzzdb/fuzzdb-1.09/Discovery/PredictableRes/ | grep raft); do
        cp $DICTS_DIRECTORY/fuzzdb/fuzzdb-1.09/Discovery/PredictableRes/$file $DICTS_DIRECTORY/restricted/raft/
    done
    echo "[*] Done"

    # Fetching cms-explorer dicts, update them and copy the updated dicts
    WgetInstall "http://cms-explorer.googlecode.com/files/cms-explorer-1.0.tar.bz2" "cms-explorer" "tar.bz2"
    mkdir -p $INSTALL_DIR/cms
    "$DICTS_DIRECTORY/update_convert_cms_explorer_dicts.sh"
    echo "[*] Cleaning Up"
    rm -rf cms-explorer
    echo "[*] Done"
    
	cd $INSTALL_DIR

    #Fetching svndigger dicts
    echo "\n[*] Fetching SVNDigger dictionaries"
	WgetInstall "http://www.mavitunasecurity.com/s/research/SVNDigger.zip" "svndigger" "zip"
    echo "[*] Done"
    
    # Copying dirbuster dicts
    echo "\n[*] Copying Dirbuster dictionaries"
    mkdir -p dirbuster
    cp -r /usr/share/dirbuster/wordlists/. dirbuster/.
    echo "[*] Done"

    cd ../
    
    # Merging svndigger and raft dicts to form hybrid dicts based on case
    echo "\n[*] Please wait while dictionaries are merged, this may take a few minutes.."
    mkdir -p $INSTALL_DIR/combined
    "./svndigger_raft_dict_merger.py"
    echo "[*] Done"

)
