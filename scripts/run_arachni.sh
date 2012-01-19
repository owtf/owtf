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

if [ $# -ne 2 -a $# -ne 3 ]; then
	echo "Usage $0 <tool_dir> <target url> (<user agent -spaces replaced by # symbol->)"
        exit
fi

TOOL_DIR=$1
URL=$2
USER_AGENT="Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0" # Default to something less obvious
if [ $3 ]; then
	USER_AGENT=$(echo $3 | sed 's/#/ /g') # Expand to real User Agent
fi

DATE=$(date +%F_%R_%S | sed 's/:/_/g')
echo "DATE=$DATE"
OUTFILE="arachni_report$DATE"
DIR=$(pwd) # Remember current dir
echo "[*] Moving to Tool directory: $TOOL_DIR"
cd $TOOL_DIR # arachni works better when run from its folder, sounds familiar? :)
#COMMAND="./arachni --only-positives --user-agent=\"$USER_AGENT\" --http-req-limit=30 --report=\"html:outfile=$OUTFILE.html\" --report=\"txt:outfile=$OUTFILE.txt\" --report=\"metareport:outfile=$OUTFILE.msf\" --report=\"ap:outfile=$OUTFILE.ap\" --report=\"xml:outfile=$OUTFILE.xml\" --report=\"afr:outfile=$OUTFILE.afr\" $URL"
COMMAND="./arachni --user-agent=\"$USER_AGENT\" --http-req-limit=20 --report=\"html:outfile=$OUTFILE.html\" --report=\"txt:outfile=$OUTFILE.txt\" --report=\"metareport:outfile=$OUTFILE.msf\" --report=\"ap:outfile=$OUTFILE.ap\" --report=\"xml:outfile=$OUTFILE.xml\" --report=\"afr:outfile=$OUTFILE.afr\" $URL"
echo
echo "[*] Running: $COMMAND"
# IMPORTANT: Running as "$COMMAND" fails totally, avoid!!!
./arachni --user-agent="$USER_AGENT" --http-req-limit=20 --report="html:outfile=$OUTFILE.html" --report="txt:outfile=$OUTFILE.txt" --report="metareport:outfile=$OUTFILE.msf" --report="ap:outfile=$OUTFILE.ap" --report="xml:outfile=$OUTFILE.xml" --report="afr:outfile=$OUTFILE.afr" $URL
#./arachni --only-positives --user-agent="$USER_AGENT" --http-req-limit=30 --report="html:outfile=$OUTFILE.html" --report="txt:outfile=$OUTFILE.txt" --report="metareport:outfile=$OUTFILE.msf" --report="ap:outfile=$OUTFILE.ap" --report="xml:outfile=$OUTFILE.xml" --report="afr:outfile=$OUTFILE.afr" $URL

REPORT_LOCATION="$TOOL_DIR/cde-package/cde-root"
echo "[*] Moving reports from $REPORT_LOCATION to $DIR"
mv $REPORT_LOCATION/$OUTFILE* $DIR
cd $DIR

# Get rid of binary garbage to extract urls correctly afterwards:
echo "[*] Removing potential binary garbage from text report .."
strings $OUTFILE.txt > arachni_report.txt

echo
echo "[*] Done!]"
