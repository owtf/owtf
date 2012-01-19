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
# * Neither the name of the <organization> nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#

echo "Upgrade Backtrack/Ubuntu? [y/n]"
read a
if [ "$a" == "y" ]; then
	for cmd in $(echo apt-get#update apt-get#upgrade apt-get#dist-upgrade); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "[*] Running: $cmd"
		$cmd
	done
fi

echo "Patch SET? [y/n]"
echo "NOTE: This is only necessary if you would like to run PHISHING plugins"
echo "NOTE 2: I cannot redistribute the patched SET version due to licence restrictions, just replace getpass.getpass with 'raw_input' calls (in SET's src directory) and you should be fine"
read a
if [ "$a" == "y" ]; then
	for cmd in $(echo cp#/root/owtf/tools/set_patched.tar.gz#/pentest/exploits/ cd#/pentest/exploits mv#set#set_old tar#xvfz#set_patched.tar.gz); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "[*] Running: $cmd"
		$cmd
	done
fi

echo "Install Selenium? [y/n]"
echo "NOTE: This is only necessary if you would like to run SELENIUM plugins"
read a
if [ "$a" == "y" ]; then
	echo "[*] Installing pip, selenium and headless driver support"
	# NOTE: rdflib seems broken via pip, thus separate install
	for cmd in $(echo apt-get#install#python-pip pip#install#selenium apt-get#install#python-rdflib apt-get#install#xvfb#xserver-xephyr pip#install#pyvirtualdisplay); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "[*] Running: $cmd"
		$cmd
	done
fi

echo "[*] In the future, there will be a separate 'get dependencies' script to download all tools/dictionaries from their websites: cannot redistribute due to licence restrictions"
