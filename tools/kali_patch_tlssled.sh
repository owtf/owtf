#!/usr/bin/env sh
#
# Description:
#       Script to fix a bug in tlssled
#
# Date:    2013-05-23
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

TLSSLED_FILE="/usr/bin/tlssled"
TLSSLED_BACKUP="$TLSSLED_FILE.backup"
if [ $(grep 'SSL_HANDSHAKE_LINES -lt 5' $TLSSLED_FILE|wc -l) -gt 0 ]; then

	echo "The current tlssled in Kali Linux needs patching to work.Do you wish to patch? [Y/n]"
	read a
	if [ "$a" != "n" ]; then
        echo "Backing up previous $TLSSLED_FILE to $TLSSLED_BACKUP.."
        cp $TLSSLED_FILE $TLSSLED_BACKUP
        echo "Patching TLSSLED :)"
        cat $TLSSLED_BACKUP | sed "s|if \[ \$SSL_HANDSHAKE_LINES -lt 5 \] ; then|if \[ \$SSL_HANDSHAKE_LINES -lt 15 \] ; then|" > $TLSSLED_FILE
    fi
else
	echo "Tlssed is already patched"
fi
