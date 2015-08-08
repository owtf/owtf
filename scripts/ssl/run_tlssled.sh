#!/usr/bin/env bash
# Description:
#       Script to run tlssled only if target speaks https
#
# Requires:
# - tlssled
# blog.taddong.com/2013/02/tlssled-v13.html
#
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2015, Bharadwaj Machiraju <name.surname@gmail.com>
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
