#!/usr/bin/env bash
#
# Description:
#       Script to run arachni with appropriate switches for basic and time-efficient web app/web server vuln detection
#	Because of above no directory brute-forcing will be done here (too slow and would be done later with dirbuster, etc)
#
# Date:    2011-10-02

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
