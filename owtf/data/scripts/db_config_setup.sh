#!/usr/bin/env sh
#
# This script creates a default config file at user specified location if it
# doesn't already exist
# Usage : $0 [rootdir] [--cfg-only]
# @param --cfg-only : Create the db.cfg file and skip postgres server setup and start

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`

cd $(dirname "$0");SCRIPT_DIR=`pwd -P`;cd $OLDPWD
. $SCRIPT_DIR/common.sh

# Simple command line argument handler.
cfg_only=false

for arg in "$@"
do
    if [ "$arg" = "--cfg-only" ]; then
        cfg_only=true
    else
        RootDir=${arg}
    fi
done

FILE_PATH=$($READLINK_CMD -f "$0")
INSTALL_DIR=$(dirname "$FILE_PATH")
RootDir=${RootDir:-$(dirname "$INSTALL_DIR")}

config_file="$RootDir/data/conf/framework.cfg"
db_config_file="$(get_config_value DATABASE_SETTINGS_FILE $config_file)"

default_db_name="owtfdb"
default_db_user="owtf_db_user"
default_db_pass=$($HEAD_CMD /dev/random -c8 | $OD_CMD -tx1 -w16 | $HEAD_CMD -n1 | cut -d' ' -f2- | tr -d ' ')

if [ ! -f ${db_config_file} ]; then
    echo "${info}[*] Please enter the database name ($default_db_name):" 
    read db_name
    db_name=${db_name:-$default_db_name}
    echo "${info}[*] Please enter the user name ($default_db_user):" 
    read db_user
    db_user=${db_user:-$default_db_user}
    echo "${info}[*] Please enter the database password (<random generated>):" 
    read db_pass
    db_pass=${db_pass:-$default_db_pass}
    
    mkdir -p "$(dirname ${db_config_file})"
    echo "${info}[*] Creating default config at $db_config_file${reset}"
    echo "${warning}[!] Don't forget to edit $db_config_file${reset}"
    echo "
# Want to create a postgres role and db. Follow steps carefully:
# + Edit this file with proper ip and port settings (No need to change if using defaults)
# + Run the db_setup.sh in scripts folder to setup a new user and new db as mentioned in this file
DATABASE_IP: 127.0.0.1
# Default postgres listens on 5432
DATABASE_PORT: 5432
DATABASE_NAME: $db_name
DATABASE_USER: $db_user
DATABASE_PASS: $db_pass" >> ${db_config_file}

    if ${cfg_only} ; then
        echo "${info}[*] Quitting ... config only!"
        exit 0
    fi

    echo "${info}[*] Do you want to create database and user as specified in $db_config_file [Y/n]?"
    read choice
    if [ choice != 'n' ]; then
        sh ${RootDir}/scripts/db_run.sh
    fi
else
    echo "${info}[*] '${db_config_file}'' Already exists! Nothing done."
fi
