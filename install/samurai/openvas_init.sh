#!/usr/bin/env bash

OWTF_RootDir=$1
OWTF_CONFIG_FILE="$OWTF_RootDir/profiles/general/default.cfg"

update_config_setting(){
  
  eval sed -i '/"$1"/d' $OWTF_CONFIG_FILE 
  echo "$1: "$2>> $OWTF_CONFIG_FILE 

}

get_config_setting(){
  grep $1 $OWTF_CONFIG_FILE | cut -f2 -d' '
}

OWTF_PGSAD=$(get_config_setting "OPENVAS_GSAD_PORT" )
OWTF_GSAD_IP=$(get_config_setting "OPENVAS_GSAD_IP")
OWTF_OPENVAS_PASSWD=$(get_config_setting "OPENVAS_PASS")
OWTF_CONFIG_ID=$(get_config_setting "OPENVAS_CONFIG_ID")