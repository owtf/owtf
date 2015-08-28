#!/usr/bin/env bash

echo "IMPORTANT: This script should be run only on the agent client (i.e. where you run OWTF from)! Would you like to continue? [y/n]"
read c
if [ "$c" == "n" ]; then
	echo "[*] Exiting"
	exit
fi

echo "Generate ssh keys? [y/n]"
read c
if [ "$c" == "y" ]; then
	cmd="ssh-keygen"
	echo "[*] Running: $cmd"
	$cmd
fi

echo "Copy remote user/host identity? -this allows password-less auth- [y/n]"
read c
if [ "$c" == "y" ]; then
	echo "[*] Please type the username"
	read USER
	echo "[*] Please type the IP or hostname of the agent server"
	read SERVER
	cmd="ssh-copy-id $USER@$SERVER"
	echo "[*] Running: $cmd"
	$cmd
fi
