#!/usr/bin/env sh
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
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

#echo "Install python-twisted? [y/n]"
#echo "See also: http://twistedmatrix.com/trac/wiki/Downloads"
#read a
#if [ "$a" == "y" ]; then
#	cmd="apt-get install python-twisted"
#	echo "[*] Running: $cmd"
#	$cmd
#fi

echo "[*] Upgrade Kali-Linux/Ubuntu? [y/n]"
read a
if [ "$a" = "y" ]; then
	for cmd in $(echo apt-get#update apt-get#upgrade apt-get#dist-upgrade); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "[*] Running: $cmd"
		$cmd
	done
fi

echo "\n[*] Installing pip"
sudo apt-get install python-pip

echo "\n[*] Install lxml? [y/n]"
#echo "Tip for Ubuntu courtesy of Mario Heiderich: Python2.7-dev is needed to compile this lib properly"
#echo "See also: http://lxml.de/installation.html"
read a
if [ "$a" = "y" ]; then
	echo "[*] Running: sudo pip install lxml"
    sudo pip install lxml
fi

echo "\n[*] Install argparse? [y/n]"
echo "[*] NOTE: This is only necessary for the DoS aux plugin for now"
read a
if [ "$a" = "y" ]; then
	echo "[*] Running: sudo pip install argparse"
    sudo pip install argparse    
fi

echo "\n[*] Install Selenium? [y/n]"
echo "[*] NOTE: This is only necessary if you would like to run SELENIUM plugins"
read a
if [ "$a" = "y" ]; then
	for cmd in $(echo sudo#pip#install#selenium sudo#pip#install#rdflib sudo#apt-get#install#xvfb#xserver-xephyr sudo#pip#install#pyvirtualdisplay); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "\n[*] Running: $cmd"
		$cmd
	done
fi

echo "\n[*] Completed installing dependencies\n"
