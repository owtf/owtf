#!/bin/bash
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

dir=$(pwd)

$dir/../../install/kali/set_config_openvas.sh


dir1="$dir/../../profiles/general/default.cfg"
port=$(grep OPENVAS_GSAD_PORT $dir1 | cut -f2 -d' ')
gsad --http-only --listen=127.0.0.1 -p $port
sleep 2

passwd=$(grep OPENVAS_PASS $dir1 | cut -f2 -d' ')

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
