#!/usr/bin/env sh

READLINK_CMD="readlink"
OD_CMD="od"
HEAD_CMD="head"
SED_CMD="sed"
if [[ "$OSTYPE" == "darwin"* ]]; then
    READLINK_CMD="greadlink"
    # Check if coreutils are installed
	which $READLINK_CMD > /dev/null
	if [ ! $? -eq 0 ]; then # Not installed
	    echo "${danger}[!] No $READLINK_CMD found! Install gnu coreutils 'brew install coreutils' !"
		exit 1
	fi
	SED_CMD="gsed"
    # Check if coreutils are installed
	which $SED_CMD > /dev/null
	if [ ! $? -eq 0 ]; then # Not installed
	    echo "${danger}[!] No $SED_CMD found! Install gnu coreutils 'brew install gnu-sed' !"
		exit 1
	fi
    OD_CMD="god"
    HEAD_CMD="ghead"

	get_postgres_server_ip() {
	    echo $(lsof -iTCP -sTCP:LISTEN -nP | awk '$1 == "postgres" && $5 == "IPv4" { print $9 }'|cut -d':' -f1)
	}

	get_postgres_server_port() {
	    echo $(lsof -iTCP -sTCP:LISTEN -nP | awk '$1 == "postgres" && $5 == "IPv4" { print $9 }'|cut -d':' -f2)
	}

	postgresql_create_user() {
		psql -Upostgres -c "CREATE USER $db_user WITH PASSWORD '$db_pass'"
	}

	postgresql_create_db() {
		psql -Upostgres -c "CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;"
	}

	postgresql_drop_user() {
	 	psql -Upostgres -c "DROP USER $db_user"
	}

	postgresql_drop_db() {
		psql -Upostgres -c "DROP DATABASE $db_name"
	}

	postgresql_check_db() {
	  	psql -l | grep -w $saved_server_dbname | grep -w $saved_server_user | wc -l
	}

fi