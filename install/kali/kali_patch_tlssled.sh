#!/usr/bin/env sh
#
# Description:
#       Script to fix a bug in tlssled

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`
. "$(dirname "$(readlink -f "$0")")/../utils.sh"

TLSSLED_FILE="/usr/bin/tlssled"
TLSSLED_BACKUP="$TLSSLED_FILE.backup"
if [ $(grep 'SSL_HANDSHAKE_LINES -lt 5' ${TLSSLED_FILE}|wc -l) -gt 0 ]; then

	echo -e "${info}\n[*] The current tlssled in Kali Linux needs patching to work.Do you wish to patch? [Y/n]${reset}"
	read a
	if [ "$a" != "n" ]; then
        echo "${info}[*] Backing up previous $TLSSLED_FILE to $TLSSLED_BACKUP..${info}"
        cp ${TLSSLED_FILE} ${TLSSLED_BACKUP}
        echo "${info}Patching TLSSLED :)${reset}"
        cat ${TLSSLED_BACKUP} | sed "s|if \[ \$SSL_HANDSHAKE_LINES -lt 5 \] ; then|if \[ \$SSL_HANDSHAKE_LINES -lt 15 \] ; then|" > ${TLSSLED_FILE}
    fi
else
	echo "${warning}[!] Tlssed is already patched! :)${reset}"
fi
