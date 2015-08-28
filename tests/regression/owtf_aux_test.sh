#!/usr/bin/env bash

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
