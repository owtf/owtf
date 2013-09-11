#!/usr/bin/env bash
#
# Description: Installation script for tools not in Backtrack or unreliable in Backtrack
# (i.e. Backtrack chose the development version instead of the stable one)
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
			if [ "$decompress_method" == "tar.gz" ]; then
				DecompressTGZ
			elif [ "$decompress_method" == "tar.bz2" ]; then
				DecompressTBZ2
			elif [ "$decompress_method" == "zip" ]; then
				DecompressZIP
			elif [ "$decompress_method" == "chmod700" ]; then
				Chmod700
			fi
		)
	else
		echo "$directory ($download_url) is already installed, skipping"
	fi
}

# This script needs to be run to download tools with potentially restrictive licensing (cannot be redistributed)
TOOLS_DIRECTORY="$(dirname $0)"
INSTALL_DIR="$TOOLS_DIRECTORY/restricted"
mkdir -p $INSTALL_DIR
(
	cd $INSTALL_DIR
	# NOTE 2: Even Arachni v.0.4.0.2 HOTFIX doesn't work (infinite loop): https://github.com/Arachni/arachni/issues/290
	# NOTE: Arachni v0.4 is still a bit unstable, it's best to stick with Arachni v0.3 in the meantime
	#WgetInstall "https://github.com/downloads/Arachni/arachni/arachni-v0.4.0.2-cde.tar.gz" "arachni-v0.4.0.2-cde"
	#The charts for arachni-v0.3 no longer show up, but this is the closest thing to "working": third party JavaScript missing?
	#WgetInstall "https://github.com/downloads/Arachni/arachni/arachni-v0.3-cde.tar.gz" "arachni-v0.3-cde" "tar.gz"

	#This is the right Arachni version to use but the shell wrapper script can't handle this structure. TODO: next release
	arachni_baseurl="http://downloads.arachni-scanner.com"
	#arachni_baseurl="http://downloads.arachni-scanner.com/nightlies"
	if [ "$(uname -a | cut -f12 -d' '|cut -f2 -d'_')" == "64" ]; then # Get arachni 64bits
		arachni_url="$arachni_baseurl/arachni-0.4.1-linux-x86_64.tar.gz"
	else # Get 32 bit version
		arachni_url="$arachni_baseurl/arachni-0.4.1-linux-i386.tar.gz"
	fi
	WgetInstall $arachni_url "arachni-v0.4.1" "tar.gz"

	# We don't need to download whatweb anymore since the Backtrack version is now stable:
	#WgetInstall "http://www.morningstarsecurity.com/downloads/whatweb-0.4.7.tar.gz" "whatweb-0.4.7" "tar.gz"
	WgetInstall "http://skipfish.googlecode.com/files/skipfish-2.09b.tgz" "skipfish" "tar.gz"
	WgetInstall "http://websecurify.googlecode.com/files/Websecurify%20Scanner%200.9.tgz" "websecurify" "tar.gz"
	WgetInstall "http://www.taddong.com/tools/BIG-IP_cookie_decoder.zip" "decoding/cookies" "zip"
	WgetInstall "http://labs.portcullis.co.uk/download/hoppy-1.8.1.tar.bz2" "hoppy-1.8.1" "tar.bz2"
	WgetInstall "http://unspecific.com/ssl/ssl-cipher-check.pl" "ssl/ssl-cipher-check" "chmod700"
	WgetInstall "http://www.taddong.com/tools/TLSSLed_v1.2.sh" "ssl/TLSSLed" "chmod700"
	TOOL_DIR="wpscan"
	if [ ! -d $TOOL_DIR ]; then
		echo "wpscan not found, downloading it.."
		mkdir -p $TOOL_DIR
		(
			cd $TOOL_DIR
			svn checkout http://wpscan.googlecode.com/svn/trunk/ ./wpscan-1.1
		)
	fi
)
yes | cp -rf "$TOOLS_DIRECTORY/signatures.txt" "/pentest/enumeration/web/httprint/linux/signatures.txt"
"$TOOLS_DIRECTORY/bt5_patch_nikto.sh"
