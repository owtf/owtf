#!/usr/bin/env bash
OWTF_RootDir=$1

. $OWTF_RootDir/scripts/openvas/openvas_init.sh "$OWTF_RootDir"

OWTF_OPENVAS_PASSWD=$(date +%s | base64 | head -c 10) #/dev/urandom did not work when called from owtf script,otherwise it works fine
                                         #Let me know if there is a wayaround

update_config_setting "OPENVAS_PASS" "$OWTF_OPENVAS_PASSWD"

if [ -d "/var/lib/openvas/users/admin" ]; then 
  openvasad -c remove_user -n admin 
fi

OWTF_OPENVAS_PASSWD=$OWTF_OPENVAS_PASSWD expect -c 'log_user 0 
spawn openvasad -c add_user -n admin -r Admin
sleep 1
expect "Enter password:" 
send "$env(OWTF_OPENVAS_PASSWD)\n"
sleep 1 '

echo