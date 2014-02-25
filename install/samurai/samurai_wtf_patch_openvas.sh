#!/usr/bin/env bash
OWTF_RootDir=$1
. $OWTF_RootDir/install/kali/openvas_init.sh "$OWTF_RootDir"

echo
echo "Installing OpenVAS, this may take a while, please be patient.."
echo

sudo -E apt-get install openvas
test -e /var/lib/openvas/CA/cacert.pem || openvas-mkcert -f
openvas-nvt-sync
test -e /var/lib/openvas/users/om || openvas-mkcert-client -n om -i
service openvas-manager stop
service openvas-scanner stop
openvassd
openvasmd --migrate
openvasmd --rebuild
killall openvassd
sleep 15
openvassd
openvasmd
openvasad
echo

. $OWTF_RootDir/install/samurai/set_config_openvas.sh "$OWTF_RootDir"

pkill -9 gsad
sleep 1
gsad --http-only --listen=$OWTF_GSAD_IP -p $OWTF_PGSAD
sleep 2

if ([[ "$choice_passwd_change" = "y" ]] || [[ -z $choice_passwd_change ]])
then
  if [ -d "/var/lib/openvas/users/admin" ]; then 
     openvasad -c remove_user -n admin
  fi
  OWTF_OPENVAS_PASSWD=$OWTF_OPENVAS_PASSWD expect -c 'log_user 0 
  spawn openvasad -c add_user -n admin -r Admin
  sleep 1
  expect "Enter password:" 
  send "$env(OWTF_OPENVAS_PASSWD)\n"
  sleep 1 '
fi
echo
echo "OpenVAS installed and configured !"
echo