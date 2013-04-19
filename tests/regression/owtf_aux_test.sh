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

if [ $# -ne 1 ]; then
	echo "Please specify OWTF directory to test!"
	echo "Syntax $0 <OWTF release directory>"
	exit
fi
OWTF_DIR=$1

# Note you can obviously run as many variants as you would like for each test ..

echo "[*] Running all defined Spear Phishing tests .."
$OWTF_DIR/owtf.py -f -o Spear_Phishing # Run as defined in config file
#$OWTF_DIR/owtf.py -f -o Spear_Phishing PHISHING_PAYLOAD=1 EMAIL_PRIORITY=no SET_EMAIL_TEMPLATE=1 # Run specific test
#$OWTF_DIR/owtf.py -f -o Spear_Phishing EMAIL_TARGET=/root/emails_new.txt # Specify alternative email targets

echo "[*] Running all defined Web tests .."
$OWTF_DIR/owtf.py -f -o Selenium_URL_Launcher # Run as defined in config file
#$OWTF_DIR/owtf.py -f -o Selenium_URL_Launcher CATEGORY=XSS BASE_URL=http://127.0.0.1/ # Run only XSS tests against the target
#$OWTF_DIR/owtf.py -f -o Selenium_URL_Launcher CATEGORY=XSS,RCE,SQLI,CHARSET BASE_URL=http://127.0.0.1/,http://target2.com # Run all tests against the 2 targets
#$OWTF_DIR/owtf.py -f -o Selenium_URL_Launcher CATEGORY=XSS,RCE BASE_URL=http://target2.com # Run tests against the defined site

echo "[*] Running all defined Bruteforce tests .."
$OWTF_DIR/owtf.py -f -o Password_Bruteforce # Run as defined in config file
#$OWTF_DIR/owtf.py -f -o Password_Bruteforce RHOST=127.0.0.1 RPORT=445 CATEGORY=SMB # A lot more useful, going for what you care about

echo "[*] Running all defined DoS tests .."
$OWTF_DIR/owtf.py -f -o Direct_DoS_Launcher # Run as defined in config file
#$OWTF_DIR/owtf.py -f -o Direct_DoS_Launcher RHOST=127.0.0.1 RPORT=80 CATEGORY=TCP,HTTP_WIN,HTTP # A lot more useful, going for what you care about
#$OWTF_DIR/owtf.py -f -o Direct_DoS_Launcher RHOST=127.0.0.1 RPORT=443 CATEGORY=TCP,HTTP_WIN,HTTP,SSL # A lot more useful, going for what you care about

echo "[*] Running all defined OS Exploits tests .."
$OWTF_DIR/owtf.py -f -o Exploit_Launcher # Run as defined in config file
#$OWTF_DIR/owtf.py -f -o Exploit_Launcher RHOST=127.0.0.1 RPORT=3306 CATEGORY=LINUX,OSX,WINDOWS SUBCATEGORY=MYSQL
#$OWTF_DIR/owtf.py -f -o Exploit_Launcher RHOST=127.0.0.1 RPORT=1521 CATEGORY=LINUX,OSX,WINDOWS SUBCATEGORY=ORACLE

# Run as defined in config file
#$OWTF_DIR/owtf.py -f -o Exploit_Launcher RHOST=127.0.0.1  RPORT=80 CATEGORY=WINDOWS SUBCATEGORY=HTTP,IIS # Run as defined in config file
