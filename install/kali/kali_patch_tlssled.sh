#!/usr/bin/env sh
#
# Description:
#       Script to fix a bug in tlssled

TLSSLED_FILE="/usr/bin/tlssled"
TLSSLED_BACKUP="$TLSSLED_FILE.backup"
if [ $(grep 'SSL_HANDSHAKE_LINES -lt 5' $TLSSLED_FILE|wc -l) -gt 0 ]; then

	echo -e "\n[*] The current tlssled in Kali Linux needs patching to work.Do you wish to patch? [Y/n]"
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
