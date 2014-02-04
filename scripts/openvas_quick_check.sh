#!/usr/bin/env bash

PGSAD=$1
PORT=$(netstat -evantupo|grep openvas|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:)

#Port-check doesn't always work as openvassd is sometimes the single process running (without openvasmd and openvasad)
#same thing happens for gsad, so it is better to check for each one

if [ "$PORT" = "" ]; then
        pkill -9 gsad
        sleep 1
        echo "Starting OpenVas Services"
        openvas-nvt-sync > /dev/null  #this prints output in weird format,same issue as above (progress status)
        openvas-scapdata-sync
        openvas-certdata-sync
        openvasmd --rebuild
        openvasmd --backup
        openvassd > /dev/null
        sleep 1
        openvasmd
        sleep 1
        openvasad
        sleep 1
        gsad --http-only --listen=127.0.0.1 -p $PGSAD
        sleep 10
else 
     if [ "$(netstat -evantupo|grep openvassd|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:)" = ""  ]; then 
        
        openvassd
     fi
     if [ "$(netstat -evantupo|grep openvasmd|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:)" = ""  ]; then
       
        openvasmd
     fi
     if [ "$(netstat -evantupo|grep openvasmd|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:)" = "" ]; then
        openvasad
     fi
     if [ "$(netstat -evantupo|grep gsad|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:)" = "" ];then
        
        gsad --http-only --listen=127.0.0.1 -p $PGSAD
        sleep 5
     fi
fi