#!/bin/bash
sudo apt-get install openvas
test -e /var/lib/openvas/CA/cacert.pem || openvas-mkcert -f
openvas-nvt-sync
test -e /var/lib/openvas/users/om || openvas-mkcert-client -n om -i
/etc/init.d/openvas-manager stop
/etc/init.d/openvas-scanner stop
pkill -9 openvas
openvassd
openvasmd --migrate
openvasmd --rebuild
killall openvassd
sleep 15
openvassd
openvasmd
openvasad
gsad --http-only --listen=127.0.0.1 -p 9392
test -e /var/lib/openvas/users/admin || openvasad -c add_user -n admin -r Admin