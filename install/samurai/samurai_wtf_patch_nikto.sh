#!/usr/bin/env sh
#
# Description:
#       Script to fix the nikto config to use a normal-looking User Agent so that we can hopefully bypass simple WAF blacklists

NIKTO_CONF_FILE="/etc/nikto.conf"
NIKTO_CONF_BACKUP="$NIKTO_CONF_FILE.backup"
if [ $(grep 'USERAGENT=Mozilla/.* (Nikto' $NIKTO_CONF_FILE|wc -l) -gt 0 ]; then
	echo -e "\n[*] Nikto is currently set to display a NIKTO USER AGENT, do you want to replace this with a normal looking one? [Y/n]"
	read a
	if [ "$a" != "n" ]; then
		echo "Backing up previous $NIKTO_CONF_FILE to $NIKTO_CONF_BACKUP.."
		cp $NIKTO_CONF_FILE $NIKTO_CONF_BACKUP
		echo "Updating nikto configuration to use a normal-looking user agent.."
		cat $NIKTO_CONF_BACKUP | sed 's|^USERAGENT=Mozilla/.* (Nikto.*$|USERAGENT=Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/20.0|' > $NIKTO_CONF_FILE
	fi
else
	echo "Nikto configuration is already set to use a normal-looking user agent"
fi
