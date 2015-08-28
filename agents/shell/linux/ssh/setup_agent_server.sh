#!/usr/bin/env bash

echo "IMPORTANT: This script should be run only on the agent server! Would you like to continue? [y/n]"
read c
if [ "$c" == "n" ]; then
	echo "[*] Exiting"
	exit
fi

echo "Install sshd? (not in Ubuntu by default) [y/n]"
read c
if [ "$c" == "y" ]; then
	cmd="apt-get install openssh-server"
	echo "[*] Running: $cmd"
	$cmd
fi

echo "Generate ssh keys? [y/n]"
read c
if [ "$c" == "y" ]; then
	cmd="ssh-keygen"
	echo "[*] Running: $cmd"
	$cmd
fi
