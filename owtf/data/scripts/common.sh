#!/usr/bin/env sh

cd $(dirname "$0");SCRIPT_DIR=`pwd -P`;cd $OLDPWD
. $SCRIPT_DIR/utils.sh

get_postgres_server_ip() {
    echo "$(sudo netstat -lptn | grep "^tcp " | grep postgres | sed 's/\s\+/ /g' | cut -d ' ' -f4 | cut -d ':' -f1)"
}

get_postgres_server_port() {
    echo "$(sudo netstat -lptn | grep "^tcp " | grep postgres | sed 's/\s\+/ /g' | cut -d ' ' -f4 | cut -d ':' -f2)"
}

postgresql_fix() {
  # remove SSL=true from the postgresql main config
  postgres_version="$(psql --version 2>&1 | tail -1 | awk '{print $3}' | sed 's/\./ /g' | awk '{print $1 "." $2}')"
  postgres_conf="$(echo 'SHOW config_file;' | sudo -u postgres psql | grep 'postgres')"
  echo "Having SSL=true in postgres config causes many errors (psycopg2 problem)"
  read -r -p "Remove SSL=true from the PostgreSQL config?[Y/n]" response
  remove_ssl=${response:-"y"}  # tolower
  case $remove_ssl in
    [yY][eE][sS]|[yY])
      sudo sed -i -e '/ssl =/ s/= .*/= false/' $postgres_conf

      echo "Restarting the postgresql service"
      # get the return values of which commands to determine the service controller
      sudo which service  >> /dev/null 2>&1
      service_bin=$?
      sudo which systemctl  >> /dev/null 2>&1
      systemctl_bin=$?
      if [ "$service_bin" != "1" ]; then
        sudo service postgresql restart
        sudo service postgresql status | grep -q "Active: active"
      elif [ "$systemctl_bin" != "1" ]; then
        sudo systemctl restart postgresql
        sudo systemctl status postgresql | grep -q "Active: active"
      else
        sudo pg_ctlcluster ${postgres_version} main restart
      fi
      ;;
    *)
      # do nothing
      ;;
  esac
}

postgresql_create_user() {
  sudo su postgres -c "psql -c \"CREATE USER $db_user WITH PASSWORD '$db_pass'\""
}
postgresql_create_db() {
  sudo su postgres -c "psql -c \"CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;\""
}
postgresql_drop_user() {
  sudo su postgres -c "psql -c \"DROP USER $db_user\""
}
postgresql_drop_db() {
  sudo su postgres -c "psql -c \"DROP DATABASE $db_name\""
}

postgresql_check_db() {
  sudo su - postgres -c "psql -l | grep -w $saved_server_dbname | grep -w $saved_server_user | wc -l"
}


. $SCRIPT_DIR/platform_config.sh
