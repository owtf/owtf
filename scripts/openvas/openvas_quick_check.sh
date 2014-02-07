#!/usr/bin/env bash
OWTF_RootDir=$1
. $OWTF_RootDir/scripts/openvas/openvas_init.sh $OWTF_RootDir

OWTF_OPENVAS_PORT=$(get_service_port "openvas")

#Port-check doesn't always work as openvassd is sometimes the single process running (without openvasmd and openvasad)
#same thing happens for gsad, so it is better to check for each one

if [ "$OWTF_OPENVAS_PORT" = "" ]; then
        pkill -9 gsad
        sleep 1
        echo "Starting OpenVas Services (Loading plugins may take time,please be patient !)"
        openvas-nvt-sync  
        openvas-scapdata-sync >/dev/null   #this prints output in weird format,same issue as progress bar
        openvas-certdata-sync > /dev/null  #not that much required,takes hours to load the data sometimes if server is down or connection is slow.
        openvasmd --rebuild
        openvasmd --backup
        echo "Loading the plugins,please wait..."
        openvassd > /dev/null
        echo "All plugins loaded."
        sleep 1
        openvasmd
        sleep 1
        openvasad
        sleep 2
        gsad --http-only --listen=$OWTF_GSAD_IP -p $OWTF_PGSAD
        sleep 10
else 
     if [ "$(get_service_port "openvassd")" = ""  ]; then 
        
        openvassd
     fi
     if [ "$(get_service_port "openvasmd")" = ""  ]; then
       
        openvasmd
     fi
     if [ "$(get_service_port "openvasmd")" = "" ]; then
      
        openvasad
     fi
     if [ "$(get_service_port "gsad")" = "" ];then
        
        gsad --http-only --listen=$OWTF_GSAD_IP -p $OWTF_PGSAD
        sleep 5
     fi
     
fi