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
echo "[*] Upgrade Samurai-WTF/Ubuntu? [Y/n]"
read a
if [ "$a" != "n" ]; then
	for cmd in $(echo apt-get#update apt-get#upgrade apt-get#dist-upgrade); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "[*] Running: $cmd"
		$cmd
	done
fi

echo "\n[*] Installing pip"
sudo apt-get install python-pip

echo "\n[*] Install lxml? [Y/n]"
#echo "Tip for Ubuntu courtesy of Mario Heiderich: Python2.7-dev is needed to compile this lib properly"
#echo "See also: http://lxml.de/installation.html"
read a
if [ "$a" != "n" ]; then
	echo "[*] Running: sudo pip install lxml"
    sudo pip install lxml
fi

echo "\n[*] Install argparse? [Y/n]"
read a
if [ "$a" != "n" ]; then
	echo "[*] Running: sudo pip install argparse"
    sudo pip install argparse    
fi

echo "\n[*] Install Jinja2 templating engine? [Y/n]"
read a
if [ "$a" != "n" ]; then
	echo "[*] Running: sudo pip install jinja2"
    sudo pip install jinja2    
fi

echo "\n[*] Install Selenium? [Y/n]"
echo "[*] NOTE: This is only necessary if you would like to run SELENIUM plugins"
read a
if [ "$a" != "n" ]; then
	for cmd in $(echo sudo#pip#install#selenium sudo#pip#install#rdflib sudo#apt-get#install#xvfb#xserver-xephyr sudo#pip#install#pyvirtualdisplay); do
		cmd=$(echo "$cmd"|tr '#' ' ')
		echo "\n[*] Running: $cmd"
		$cmd
	done
fi

echo "\n[*] Install dependencies needed for Inbound Proxy? [Y/n]"
read a
if [ "$a" != "n" ]; then
    sudo pip install tornado pycurl
fi

echo "\n[*] Completed installing dependencies\n"