#!/usr/bin/env bash
#
# Description:
#       Script to run nikto with appropriate switches for basic and time-efficient web app/web server vuln detection
#	Because of above no directory brute-forcing will be done here (too slow and would be done later with dirbuster, etc)
#
# Date:    2011-10-02
# Version: 2.0
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


if [ $# -ne 3 -a $# -ne 4 -a $# -ne 5 ]; then
        echo "Usage $0 <tool_dir> <target_ip> <proxy> (<target_port>) (<target hostname>)"
	echo "Tip: Change the USER_AGENT on nikto.conf to something normal.."
        exit
fi

PORT=80
if [ $4 ]; then
        PORT=$4
fi

TOOL_DIR=$1
IP=$2
PROXY=$3
PROXY_IP=$(echo $PROXY | cut -d ":" -f 1)
PROXY_PORT=$(echo $PROXY | cut -d ":" -f 2)
HOST_NAME=$ip
NIKTO_NOLOOKUP="-nolookup"
if [ $5 ] && [ "$5" != "$ip" ]; then
        HOST_NAME=$5
        NIKTO_NOLOOKUP="" #Host name passed: must look up
fi

NIKTO_SSL=""
SSL_HANDSHAKE_LINES=$((sleep 5 ; echo -e "^C" 2> /dev/null) |  openssl s_client -connect $HOST_NAME:$PORT 2> /dev/null | wc -l)
if [ $SSL_HANDSHAKE_LINES -gt 15 ]; then # SSL Handshake successful, proceed with nikto -ssl switch
        NIKTO_SSL="-ssl"
fi

# Temporary nikto config file
NIKTO_CONF_FILE="/etc/nikto.conf"
# Abe: Adding pid to temporary config to avoid potential concurrent process issues
PID=$$
TEMP_NIKTO_CONF_FILE="/tmp/temp_owtf.$PID.nikto.conf"
if [ -f $TEMP_NIKTO_CONF_FILE ]; then
    rm $TEMP_NIKTO_CONF_FILE
fi
cp $NIKTO_CONF_FILE $TEMP_NIKTO_CONF_FILE
#echo "PROXYHOST=$PROXY_IP" >> $TEMP_NIKTO_CONF_FILE
echo "PROXYPORT=$PROXY_PORT" >> $TEMP_NIKTO_CONF_FILE

DATE=$(date +%F_%R:%S | sed 's/:/_/g')
OUTFILE="nikto$DATE"
LOG_XML=$OUTFILE.xml
DIR=$(pwd) # Remember current dir
cd "$TOOL_DIR" # Nikto needs to be run from its own folder
echo $TOOL_DIR
if [ ! -f ./nikto.pl ]; then # Kali linux hack
	cp /usr/bin/nikto /usr/share/nikto/nikto.pl # Ensure the executable is on the right place, so that below runs even if the user did not run the install script
fi
# There is a import error when running from Nikto dir i.e /usr/share/nikto
# Abe: somehow the -useproxy option makes nikto abort with '+ No web server found on', removing "-useproxy" while we figure that out
#COMMAND="nikto $NIKTO_NOLOOKUP -evasion 1 $NIKTO_SSL -config $TEMP_NIKTO_CONF_FILE  -useproxy -host $HOST_NAME -port $PORT -output $DIR/$LOG_XML -Format xml"
COMMAND="nikto $NIKTO_NOLOOKUP -evasion 1 $NIKTO_SSL -config $TEMP_NIKTO_CONF_FILE -host $HOST_NAME -port $PORT -output $DIR/$LOG_XML -Format xml"
echo "[*] Running: $COMMAND"
$COMMAND

echo
echo "[*] Done!]"
