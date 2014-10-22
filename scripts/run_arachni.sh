#!/usr/bin/env bash
#
# Description:
#       Script to run arachni with appropriate switches for basic and time-efficient web app/web server vuln detection
#	Because of above no directory brute-forcing will be done here (too slow and would be done later with dirbuster, etc)
#
# Date:    2011-10-02
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

if [ $# -ne 4 -a $# -ne 5 ]; then
	echo "Usage $0 <tool_bin> <reporter_bin> <target url> <proxy> (<user agent -spaces replaced by # symbol->)"
        exit
fi

TOOL_BIN=$1
REPORTER_BIN=$2
URL=$3
PROXY=$4
USER_AGENT="Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0" # Default to something less obvious
if [[ -z "$5" ]]; then
	USER_AGENT=$(echo $4 | sed 's/#/ /g') # Expand to real User Agent
fi


DATE=$(date +%F_%R_%S | sed 's/:/_/g')
echo "DATE=$DATE"
OUTFILE="arachni_report$DATE"
DIR=$(pwd)
#COMMAND="$TOOL_BIN --only-positives --user-agent=\"$USER_AGENT\" --http-req-limit=30 --report=\"html:outfile=$OUTFILE.html\" --report=\"txt:outfile=$OUTFILE.txt\" --report=\"metareport:outfile=$OUTFILE.msf\" --report=\"ap:outfile=$OUTFILE.ap\" --report=\"xml:outfile=$OUTFILE.xml\" --report=\"afr:outfile=$OUTFILE.afr\" $URL"
COMMAND="./$TOOL_BIN --http-user-agent=\"$USER_AGENT\" --http-request-concurrency=20 --report-save-path=\"$OUTFILE.afr\" --http-proxy=$PROXY $URL"
echo
echo "[*] Running: $COMMAND"
# IMPORTANT: Running as "$COMMAND" fails totally, avoid!!!
$TOOL_BIN --http-user-agent="$USER_AGENT" --http-request-concurrency=20 --report-save-path="$DIR/$OUTFILE.afr" --http-proxy=$PROXY $URL
#./arachni --only-positives --user-agent="$USER_AGENT" --http-req-limit=30 --report="html:outfile=$OUTFILE.html" --report="txt:outfile=$OUTFILE.txt" --report="metareport:outfile=$OUTFILE.msf" --report="ap:outfile=$OUTFILE.ap" --report="xml:outfile=$OUTFILE.xml" --report="afr:outfile=$OUTFILE.afr" $URL

COMMAND="./$REPORTER_BIN --reporter=\"html:outfile=$OUTFILE.html.zip\" --reporter=\"txt:outfile=$OUTFILE.txt\" --reporter=\"json:outfile=$OUTFILE.json\" --reporter=\"ap:outfile=$OUTFILE.ap\" --reporter=\"xml:outfile=$OUTFILE.xml\" \"$DIR/$OUTFILE.afr\""
echo
echo "[*] Running: $COMMAND"
$REPORTER_BIN --reporter="html:outfile=$OUTFILE.html.zip" --reporter="txt:outfile=$OUTFILE.txt" --reporter="json:outfile=$OUTFILE.json" --reporter="ap:outfile=$OUTFILE.ap" --reporter="xml:outfile=$OUTFILE.xml" "$DIR/$OUTFILE.afr"

# Arachni produces compressed html report now
unzip "$OUTFILE.html.zip" -d "html_report"

# Get rid of binary garbage to extract urls correctly afterwards:
echo "[*] Removing potential binary garbage from text report .."
strings $OUTFILE.txt > arachni_report.txt

echo
echo "[*] Done!"
