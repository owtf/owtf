#!/usr/bin/env bash
# Description:
#       Script to run tlssled only if target speaks https
#
# Requires:
# - tlssled
# blog.taddong.com/2013/02/tlssled-v13.html

if [ $# -ne 3 ]; then
   echo "Usage: $0 <full path to tlssled> IP PORT"
   exit
fi

TLSSLED=$1
HOST=$2
PORT=$3
RENEG_FILE='reneg.log'
RENEG_FILE_ERRORS='reneg_errors.log'

#echo "Before handshake.."
# Check if the target service speaks SSL/TLS (& check renegotiation)
(echo R; sleep 5) | openssl s_client -connect $HOST:$PORT > $RENEG_FILE 2> $RENEG_FILE_ERRORS &
pid=$!
sleep 5
#echo "After handshake.."

SSL_HANDSHAKE_LINES=$(cat $RENEG_FILE | wc -l)

if [ $SSL_HANDSHAKE_LINES -lt 15 ] ; then
        # SSL handshake failed - Non SSL/TLS service
        # If the target service does not speak SSL/TLS, openssl does not terminate
        kill -s SIGINT ${pid}

	echo
	echo "[*] TLSSLED skipped!: The host $HOST does not appear to speak SSL/TLS on port: $PORT"
	echo
	exit
else # SSL Handshake successful, proceed with check
	echo
	echo "[*] SSL Handshake Check OK: The host $HOST appears to speak SSL/TLS on port: $PORT"
	echo
fi

$TLSSLED "$HOST" "$PORT"
