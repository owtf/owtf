#!/usr/bin/env bash
#
# Description:
#       Script to run wapiti with appropriate switches for basic and
#       time-efficient web app/web server vuln detection
#
# Date:    2014-08-09

TOOL_BIN=$1
URL=$2

DATE=$(date +%F_%R_%S | sed 's/:/_/g')
OUTPUTFILE="wapiti_report$DATE"
DIR=$(pwd)
FORMAT="xml"
COMMAND="$TOOL_BIN $URL -f $FORMAT --output $OUTPUTFILE.$FORMAT"

echo "[*] Running: $COMMAND"

$COMMAND
