#!/usr/bin/env bash

CUR_DIR=$(pwd) # Remember current dir
OWTF_DIR="$CUR_DIR/../../../../../../../"
CONFIG_FILE="$OWTF_DIR/profiles/general/default.cfg"
HTML_FORMAT_ID="6c248850-1f62-11e1-b082-406186ea4fc5"



get_config_setting(){
  grep $1 $CONFIG_FILE | cut -f2 -d' '
}

get_progress_status(){
  omp -u admin -w $1 -G | grep $2 |sed 's/  */#/g'|cut -f2,3 -d'#'
}

get_service_port(){
  netstat -evantupo|grep $1|grep LISTEN| sed 's/  */#/g'|cut -f4 -d# | cut -f2 -d:
}

update_config_setting(){
  echo "$1: "$2>> $CONFIG_FILE 
  
}

CONFIG_ID=$(get_config_setting "OPENVAS_CONFIG_ID")
PGSAD=$(get_config_setting "OPENVAS_GSAD_PORT")


if [[ "$CONFIG_ID" = "" ]]
then
 CONFIG_ID="daba56c8-73ec-11df-a475-002264764cea"
 update_config_setting "OPENVAS_CONFIG_ID" "$CONFIG_ID"
fi

if [[ "$PGSAD" = "" ]]
then
 PGSAD="9392"
 update_config_setting "OPENVAS_GSAD_PORT" "$PGSAD"
fi
