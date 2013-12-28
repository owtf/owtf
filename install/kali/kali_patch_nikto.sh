#!/usr/bin/env sh
#
# Description:
#       Script to fix the nikto config to use a normal-looking User Agent so that we can hopefully bypass simple WAF blacklists
#
# Date:    2012-09-24
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

NIKTO_CONF_FILE="/etc/nikto.conf"
NIKTO_CONF_BACKUP="$NIKTO_CONF_FILE.backup"
if [ $(grep 'USERAGENT=Mozilla/.* (Nikto' $NIKTO_CONF_FILE|wc -l) -gt 0 ]; then
	echo "Nikto is currently set to display a NIKTO USER AGENT, do you want to replace this with a normal looking one? [Y/n]"
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
