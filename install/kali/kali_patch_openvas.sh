#!/bin/bash
. $(pwd)/../../install/kali/openvas_init.sh

echo
echo "Installing OpenVAS, this may take a while, please be patient.."
echo

sudo apt-get install openvas
test -e /var/lib/openvas/CA/cacert.pem || openvas-mkcert -f
openvas-nvt-sync
test -e /var/lib/openvas/users/om || openvas-mkcert-client -n om -i
/etc/init.d/openvas-manager stop
/etc/init.d/openvas-scanner stop
openvassd
openvasmd --migrate
openvasmd --rebuild
killall openvassd
sleep 15
openvassd
openvasmd
openvasad
echo

. $CUR_DIR/../../install/kali/set_config_openvas.sh

pkill -9 gsad
sleep 1
gsad --http-only --listen=127.0.0.1 -p $port
sleep 2

if ([[ "$choice_passwd_change" = "y" ]] || [[ -z $choice_passwd_change ]])
then
  if [ -d "/var/lib/openvas/users/admin" ]; then 
     openvasad -c remove_user -n admin
  fi
  passwd=$passwd expect -c 'log_user 0 
  spawn openvasad -c add_user -n admin -r Admin
  sleep 1
  expect "Enter password:" 
  send "$env(passwd)\n"
  sleep 1 '
fi
echo
echo "OpenVAS installed and configured !"
echo
