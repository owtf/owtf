#!/usr/bin/env bash

if [ $# -lt 1 ]; then
	echo "Syntax: $0 <file with urls.txt> (proxy_ip: default 127.0.0.1) (proxy_port: default 8080)"
	exit
fi

FILE=$1
PROXY_IP="127.0.0.1"
PROXY_PORT="8080"
if [ $2 ]; then
	PROXY_IP=$2	
fi
if [ $3 ]; then
	PROXY_PORT=$3
fi

COUNT=0
for i in $(cat $FILE); do 
	COUNT=$(($COUNT + 1))
	echo "$COUNT - Sending $i to proxy .."
	curl -k "$i" --proxy 127.0.0.1:8080 -o /dev/null
done
