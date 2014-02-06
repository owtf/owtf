#!/usr/bin/env bash

export CUR_DIR=$(pwd)
export CONFIG_FILE="$CUR_DIR/../../profiles/general/default.cfg"
export port=$(grep OPENVAS_GSAD_PORT $CONFIG_FILE | cut -f2 -d' ')
export passwd=$(grep OPENVAS_PASS $CONFIG_FILE | cut -f2 -d' ')
export config_id=$(grep OPENVAS_CONFIG_ID $CONFIG_FILE | cut -f2 -d' ')

update_config_setting(){

  sed -i '/$1/d' $CONFIG_FILE
  echo "$1: "$2>> $CONFIG_FILE 

}