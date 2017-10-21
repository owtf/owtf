#!/usr/bin/env sh
#
# This script creates a new user and a database as specified in
# /framework/config/framework_config.cfg

cd $(dirname "$0");SCRIPT_DIR=`pwd -P`;cd $OLDPWD
. $SCRIPT_DIR/common.sh

# Bail out if action is not provided
if [ "$1" = "" ]
then
    echo "Usage: $0 [action]"
    echo
    echo "[*] To create database and user"
    echo "./$0 \"init\""
    echo
    echo "[*] To remove database and user"
    echo "./$0 \"clean\""
    exit 1
fi


Action=$1

FILE_PATH=$($READLINK_CMD -f "$0")
SCRIPTS_DIR=$(dirname "$FILE_PATH")
RootDir=$(dirname "$SCRIPTS_DIR")

if [ "$2" = "" ]; then
    config_file="$RootDir/data/conf/framework.cfg"
    db_config_file="$(get_config_value DATABASE_SETTINGS_FILE $config_file)"
else
    db_config_file="$2"
fi

db_name=$(get_config_value DATABASE_NAME $db_config_file)
db_user=$(get_config_value DATABASE_USER $db_config_file)
db_pass=$(get_config_value DATABASE_PASS $db_config_file)

echo
echo "------------------------- OWTF Database Helper Script -------------------------"
echo "                    Helps in creation of user and database                     "
echo "-------------------------------------------------------------------------------"
echo
echo "[+] Ensure that you have required values in $db_config_file"
echo
echo "Press Enter to continue"

read dummy

if [ "$Action" = "init" ]
then
    psql -Upostgres -c "CREATE USER $db_user WITH PASSWORD '$db_pass'"
    psql -Upostgres -c "CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;"
    sudo su postgres -c "psql -c \"CREATE USER $db_user WITH PASSWORD '$db_pass'\""
    sudo su postgres -c "psql -c \"CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;\""
elif [ "$Action" = "clean" ]
then
    psql -Upostgres -c "DROP DATABASE $db_name"
    psql -Upostgres -c "DROP USER $db_user"
    sudo su postgres -c "psql -c \"DROP DATABASE $db_name\""
    sudo su postgres -c "psql -c \"DROP USER $db_user\""
fi
