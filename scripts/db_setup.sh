action="init"

postgres_server_ip="127.0.0.1"
db_name="owtf_db"
db_user="owtf_db_user"
db_pass="jgZKW33Q+HZk8rqylZxaPg1lbuNGHJhgzsq3gBKV32g="
postgres_server_port=5432
postgres_version="$(psql --version 2>&1 | tail -1 | awk '{print $3}' | $SED_CMD 's/\./ /g' | awk '{print $1 "." $2}')"


# =======================================
#   DATABASE setup
# =======================================

# Check if postgresql service is running or not
postgresql_check_running_status() {
    postgres_ip_status=$(get_postgres_server_ip)
    if [ -z "$postgres_ip_status" ]; then
        echo "PostgreSQL server is not running."
        echo "Please start the PostgreSQL server and rerun."
        echo "For Kali/Debian like systems, try sudo service postgresql start or sudo systemctl start postgresql "
        echo "For macOS, use pg_ctl -D /usr/local/var/postgres start "
    else
        echo "[+] PostgreSQL server is running ${postgres_server_ip}:${postgres_server_port} :)"
    fi
}

# returns postgresql service IP
get_postgres_server_ip() {
    echo "$(sudo netstat -lptn | grep "^tcp " | grep postgres | sed 's/\s\+/ /g' | cut -d ' ' -f4 | cut -d ':' -f1)"
}

postgresql_create_user() {
    sudo su postgres -c "psql -c \"CREATE USER $db_user WITH PASSWORD '$db_pass'\""
}

postgres_alter_user_password() {
    sudo su postgres -c "psql postgres -tc \"ALTER USER $db_user WITH PASSWORD '$db_pass'\""
}

postgresql_create_db() {
    sudo su postgres -c "psql -c \"CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;\""
}

postgresql_check_user() {
    cmd="$(psql -l | grep -w $db_name | grep -w $db_user | wc -l | xargs)"
    if [ "$cmd" != "0" ]; then
        return 1
    else
        return 0
    fi
}

postgresql_drop_user() {
    sudo su postgres -c "psql -c \"DROP USER $db_user\""
}

postgresql_drop_db() {
    sudo su postgres -c "psql -c \"DROP DATABASE $db_name\""
}

postgresql_check_db() {
    cmd="$(psql -l | grep -w $db_name | wc -l | xargs)"
    if [ "$cmd" != "0" ]; then
        return 1
    else
        return 0
    fi
}


db_setup() {
    # Check if the postgres server is running or not.
    postgresql_check_running_status
    # postgres server is running perfectly fine begin with db_setup.
    # Create a user $db_user if it does not exist
    if [ postgresql_check_user == 1 ]; then
        echo "[+] User $db_user already exist."
        # User $db_user already exist in postgres database change the password
        continue
    else
        # Create new user $db_user with password $db_pass
        postgresql_create_user
    fi
    # Create database $db_name if it does not exist.
    if [ postgresql_check_db == 1 ]; then
       echo "[+] Database $db_name already exist."
       continue
    else
       # Either database does not exists or the owner of database is not $db_user
       # Create new database $db_name with owner $db_user
       postgresql_create_db
    fi
}

