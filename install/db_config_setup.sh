#!/usr/bin/env sh
#
# This script creates a default config file at user specified location if it
# doesn't already exist
# Usage : $0 [rootdir] [--cfg-only]
# @param --cfg-only : Create the db.cfg file and skip postgres server setup and start

get_config_value(){

    parameter=$1
    file=$2

    echo "$(grep -i $parameter $file | sed  "s|$parameter: ||g;s|~|$HOME|g")"
}

# Simple command line argument handler.
cfg_only=false

for arg in "$@"
do
    if [ "$arg" = "--cfg-only" ]; then
        cfg_only=true
    else
        RootDir=$arg
    fi
done

FILE_PATH=$(readlink -f "$0")
INSTALL_DIR=$(dirname "$FILE_PATH")
RootDir=${RootDir:-$(dirname "$INSTALL_DIR")}

config_file="$RootDir/framework/config/framework_config.cfg"
db_config_file="$(get_config_value DATABASE_SETTINGS_FILE $config_file)"

db_name="owtfdb"
db_user="owtf_db_user"
db_pass=$(head /dev/random -c8 | od -tx1 -w16 | head -n1 | cut -d' ' -f2- | tr -d ' ')

if [ ! -f $db_config_file ]; then
    mkdir -p "$(dirname $db_config_file)"
    echo "[*] Creating default config at $db_config_file"
    echo "[*] Don't forget to edit $db_config_file"
    echo "
# Want to create a postgres role and db. Follow steps carefully:
# + Edit this file with proper ip and port settings (No need to change if using defaults)
# + Run the db_setup.sh in scripts folder to setup a new user and new db as mentioned in this file
DATABASE_IP: 127.0.0.1
# Default postgres listens on 5432
DATABASE_PORT: 5432
DATABASE_NAME: $db_name
DATABASE_USER: $db_user
DATABASE_PASS: $db_pass" >> $db_config_file

    if $cfg_only ; then
        exit 0
    fi

    echo "[*] Do you want to create database and user as specified in $db_config_file [Y/n]?"
    read choice
    if [ choice != 'n' ]; then
        $RootDir/scripts/db_run.sh
    fi
fi
