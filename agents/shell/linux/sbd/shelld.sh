#!/usr/bin/env bash

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
