#!/usr/bin/env bash



OWTF_RootDir=$1
OWTF_CONFIG_FILE="$OWTF_RootDir/profiles/general/default.cfg"
HTML_FORMAT_ID="6c248850-1f62-11e1-b082-406186ea4fc5"



get_config_setting(){
  grep $1 $OWTF_CONFIG_FILE | cut -f2 -d' '
}

get_progress_status(){
  omp -u admin -w $1 -G | grep $2 |sed 's/  */#/g'|cut -f2,3 -d'#'
}

get_service_port(){
  netstat -evantupo|grep $1|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:
}

update_config_setting(){
  echo "$1: "$2>> $OWTF_CONFIG_FILE 
  
}

OWTF_CONFIG_ID=$(get_config_setting "OPENVAS_CONFIG_ID")
OWTF_PGSAD=$(get_config_setting "OPENVAS_GSAD_PORT")
OWTF_GSAD_IP=$(get_config_setting "OPENVAS_GSAD_IP")

if [[ "$OWTF_CONFIG_ID" = "" ]]
then
 OWTF_CONFIG_ID="daba56c8-73ec-11df-a475-002264764cea"
 update_config_setting "OPENVAS_CONFIG_ID" "$OWTF_CONFIG_ID"
fi

if [[ "$OWTF_PGSAD" = "" ]]
then
 OWTF_PGSAD="9392"
 update_config_setting "OPENVAS_GSAD_PORT" "$OWTF_PGSAD"
fi

if [[ "$OWTF_GSAD_IP" = "" ]]
then
  OWTF_GSAD_IP="127.0.0.1"
  update_config_setting "OPENVAS_GSAD_IP" "127.0.0.1"
fi
