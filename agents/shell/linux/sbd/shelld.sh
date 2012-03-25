#!/usr/bin/env bash
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

DIR=$(dirname $0) # Load sbd and config from shell directory
echo "OWTF Agent - persistent linux shell based on sbd: Shared password encrypted channel with persistent shell access"
echo "Password and port are configurable from the command line interface (CLI) or a shelld.cfg config file"
if [ $# -ne 1 ]; then
	echo "Syntax $0 <port or config file>"
	exit
fi

if [ -f $1 ]; then # Config file supplied, read values from there
	CONFIG=$DIR/$1
	PORT=$(grep PORT $CONFIG | cut -f2 -d=)
	PASSWORD=$(grep PASSWORD $CONFIG | cut -f2 -d=)
else # No config supplied, read parameters from commandline
	PORT=$1
	echo "Type a password for the agent"
	read PASSWORD
	clear
fi

echo "Starting persistent listener.."
$DIR/sbd -nvlp $PORT -e /bin/sh -r0 -k $PASSWORD