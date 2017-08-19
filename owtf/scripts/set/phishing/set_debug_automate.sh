#!/usr/bin/env bash

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
