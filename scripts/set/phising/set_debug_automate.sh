#!/bin/sh
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

if [ $# -ne 2 ]; then
	echo "Syntax: $0 <set_dir> <set_automate_instructions>"
	exit
fi

SET=$1
INSTRUCTIONS=$2
if [ ! -d $SET ]; then
	echo "Invalid SET path: '$SET'"
	exit
fi 

if [ ! -f $INSTRUCTIONS ]; then
	echo "Invalid instructions path: '$INSTRUCTIONS'"
	exit
fi

PAUSE=1
COMMAND="( sleep $PAUSE ; echo \"y\"; sleep $PAUSE;"
for instruction in $(cat $INSTRUCTIONS | sed 's/ /##/g'); do
	ins=$(echo $instruction|sed 's/##/ /g')
	insname=$(echo $ins|cut -f1 -d" ")
	insvalue=$(echo $ins|cut -f2 -d" ")
	CMD=""
	if [ "$ins" == "Control+C" ]; then # Perform Control + C
		CMD="echo \"Sending Control+C..\" >&2; echo -e \"^C\"; sleep $PAUSE;"
	fi
	if [ "$insname" == "sleep" ]; then # Sleep the time specified
		CMD="echo \"Sleeping $insvalue seconds ..\" >&2 ; sleep $insvalue;"
	fi
	if [ "$CMD" == "" ]; then # The command is nothing special, pass straight to SET
		CMD="echo \"Sending $ins ..\" >&2 ; echo \"$ins\"; sleep $PAUSE;"
	fi
	COMMAND="$COMMAND $CMD"
done

COMMAND="$COMMAND)" 

echo "$COMMAND" > settmp.sh
echo "Commands to use:"
echo $COMMAND
chmod 700 settmp.sh
dir=$(pwd)
echo "[*] Going to SET's directory .."
cd "$SET"
echo "[*] running script .."
"$dir/settmp.sh" | ./set
