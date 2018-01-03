#!/usr/bin/env sh
# This script runs postgres server in very stupid ways, this script is tested
# extensively on Kali

cd $(dirname "$0");SCRIPT_DIR=`pwd -P`;cd $OLDPWD
. $SCRIPT_DIR/common.sh


FILE_PATH=$($READLINK_CMD -f "$0")
SCRIPTS_DIR=$(dirname "$FILE_PATH")
RootDir=$(dirname "$SCRIPTS_DIR")

config_file="$RootDir/../settings.py"
db_config_file="$(get_db_config_file $config_file $1)"

if [ ! -f "$db_config_file" ]; then
    exit 1
fi

# Saved postgres settings
saved_server_ip="$(get_config_value DATABASE_IP $db_config_file)"
saved_server_port="$(get_config_value DATABASE_PORT $db_config_file)"
saved_server_dbname="$(get_config_value DATABASE_NAME $db_config_file)"
saved_server_user="$(get_config_value DATABASE_USER $db_config_file)"
saved_server_pass="$(get_config_value DATABASE_PASS $db_config_file)"

# Check if postgres is running
postgres_server_ip='127.0.0.1'
postgres_server_port=5432

# PostgreSQL version
postgres_version="$(psql --version 2>&1 | tail -1 | awk '{print $3}' | $SED_CMD 's/\./ /g' | awk '{print $1 "." $2}')"

if [ -z "$postgres_server_ip" ]; then
    echo "${info}[+] PostgreSQL server is not running."
    echo "${info}[+] Can I start db server for you? [Y/n]"
    read choice
    if [ "$choice" != "n" ]; then
        sudo which service  >> /dev/null 2>&1
        service_bin=$?
        sudo which systemctl  >> /dev/null 2>&1
        systemctl_bin=$?
        if [ "$service_bin" = "0" ]; then
            sudo service postgresql start
            sudo service postgresql status | grep -q "Active: active"
            status_exitcode="$?"
        elif [ "$systemctl_bin" = "0" ]; then
            sudo systemctl start postgresql
            sudo systemctl status postgresql | grep -q "Active: active"
            status_exitcode="$?"
        elif [ "$systemctl_bin" != "0" ] && [ "$service_bin" != "0" ]; then
            echo "${info}[+] Using pg_ctlcluster to start the server."
            sudo pg_ctlcluster ${postgres_version} main start
        else
            echo "${info}[+] We couldn't determine how to start the postgres server, please start it and rerun this script"
            exit 1
        fi
        if [ "$status_exitcode" != "0" ]; then
            echo "${info}[+] Starting failed because postgreSQL service is not available!"
            echo "${info}[+] Run # sh scripts/start_postgres.sh and rerun this script"
            exit 1
        fi
    else
        echo "${info}[+] On DEBIAN based distro [i.e Kali, Ubuntu etc..]"
        echo "          sudo service postgresql start"
        echo "${info}[+] On RPM based distro [i.e Fedora etc..]"
        echo "          sudo systemctl start postgresql"
        exit 1
    fi
else
    echo "${info}[+] PostgreSQL server is running ${postgres_server_ip}:${postgres_server_port} :)"
fi
