#!/usr/bin/env bash

. $(pwd)/../../../../../../../scripts/openvas/openvas_init.sh

passwd=$(date +%s | base64 | head -c 10) #/dev/urandom did not work when called from owtf script,otherwise it works fine
                                         #Let me know if there is a wayaround

update_config_setting "OPENVAS_PASS" "$passwd"

if [ -d "/var/lib/openvas/users/admin" ]; then 
  openvasad -c remove_user -n admin 
fi

passwd=$passwd expect -c 'log_user 0 
spawn openvasad -c add_user -n admin -r Admin
sleep 1
expect "Enter password:" 
send "$env(passwd)\n"
sleep 1 '

echo