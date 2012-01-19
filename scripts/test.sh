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

# Note you can obviously run as many variants as you would like for each test ..

echo "[*] Running all defined Spear Phising tests .."
/root/owtf/owtf.py -f -o Spear_Phising # Run as defined in config file
#/root/owtf/owtf.py -f -o Spear_Phising PHISHING_PAYLOAD=1 EMAIL_PRIORITY=no SET_EMAIL_TEMPLATE=1 # Run specific test
#/root/owtf/owtf.py -f -o Spear_Phising EMAIL_TARGET=/root/emails_new.txt # Specify alternative email targets

echo "[*] Running all defined Web tests .."
/root/owtf/owtf.py -f -o Selenium_URL_Launcher # Run as defined in config file
#/root/owtf/owtf.py -f -o Selenium_URL_Launcher CATEGORY=XSS BASE_URL=http://127.0.0.1/ # Run only XSS tests against the target
#/root/owtf/owtf.py -f -o Selenium_URL_Launcher CATEGORY=XSS,RCE,SQLI,CHARSET BASE_URL=http://127.0.0.1/,http://target2.com # Run all tests against the 2 targets
#/root/owtf/owtf.py -f -o Selenium_URL_Launcher CATEGORY=XSS,RCE BASE_URL=http://target2.com # Run tests against the defined site

echo "[*] Running all defined Bruteforce tests .."
/root/owtf/owtf.py -f -o Password_Bruteforce # Run as defined in config file
#/root/owtf/owtf.py -f -o Password_Bruteforce RHOST=127.0.0.1 RPORT=445 CATEGORY=SMB # A lot more useful, going for what you care about

echo "[*] Running all defined DoS tests .."
/root/owtf/owtf.py -f -o Direct_DoS_Launcher # Run as defined in config file
#/root/owtf/owtf.py -f -o Direct_DoS_Launcher RHOST=127.0.0.1 RPORT=80 CATEGORY=TCP,HTTP_WIN,HTTP # A lot more useful, going for what you care about
#/root/owtf/owtf.py -f -o Direct_DoS_Launcher RHOST=127.0.0.1 RPORT=443 CATEGORY=TCP,HTTP_WIN,HTTP,SSL # A lot more useful, going for what you care about

echo "[*] Running all defined OS Exploits tests .."
/root/owtf/owtf.py -f -o Exploit_Launcher # Run as defined in config file
#/root/owtf/owtf.py -f -o Exploit_Launcher RHOST=127.0.0.1  RPORT=80 CATEGORY=WINDOWS SUBCATEGORY=HTTP,IIS # Run as defined in config file


