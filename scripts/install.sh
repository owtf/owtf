#!/usr/bin/env sh

#set -e

SCRIPT_DIR="$(pwd -P)/scripts"
OWTF_DIR="${HOME}/.owtf"
ROOT_DIR="$(dirname $SCRIPT_DIR)/owtf"
CWD="$(dirname $ROOT_DIR)"

. ${SCRIPT_DIR}/platform_config.sh
export NVM_DIR="${HOME}/.nvm"

# ======================================
#   ESSENTIAL
# ======================================
yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


if [ ! -f "${CWD}/Makefile" ]; then
    die "Exiting: no Makefile found"
fi

[ -d $OWTF_DIR ] || mkdir $OWTF_DIR


# ======================================
#  COLORS
# ======================================
bold=$(tput bold)
reset=$(tput sgr0)

danger=${bold}$(tput setaf 1)   # red
warning=${bold}$(tput setaf 3)  # yellow
info=${bold}$(tput setaf 6)     # cyan
normal=${bold}$(tput setaf 7)   # white

# =======================================
#   Default variables
# =======================================
user_agent='Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/15.0'

action="init"

certs_folder="${OWTF_DIR}/proxy/certs"
ca_cert="${OWTF_DIR}/proxy/certs/ca.crt"
ca_key="${OWTF_DIR}/proxy/certs/ca.key"
ca_pass_file="${OWTF_DIR}/proxy/certs/ca_pass.txt"
ca_key_pass="$(openssl rand -base64 16)"

db_user="owtf_db_user"
db_name="owtf_db"
db_pass="$(openssl rand -base64 32)"
postgres_server_ip="127.0.0.1"
postgres_server_port=5432
postgres_version="$(psql --version 2>&1 | tail -1 | awk '{print $3}' | $SED_CMD 's/\./ /g' | awk '{print $1 "." $2}')"


# =======================================
#   COMMON FUNCTIONS
# =======================================

create_directory() {
    if [ ! -d $1 ]; then
      mkdir -p $1;
      return 1
    else
      return 0
    fi
}

check_sudo() {
    timeout 2 sudo id && sudo=1 || sudo=0
    return $sudo
}

install_in_dir() {
    tmp=$PWD
    if [ $(create_directory $1) ]; then
        cd $1
        echo "Running command $2 in $1"
        $2
    else
        echo "${warning}[!] Directory $1 already exists, so skipping installation for this${reset}"
    fi
    cd $tmp
}

check_debian() {
    if [ -f "/etc/debian_version" ]; then
        debian=1
    else
        debian=0
    fi
    return $debian
}

copy_dirs() {
    dest=$2
    src=$1
    if [ ! -d $dest ]; then
        cp -r $src $dest
    else
        echo "${warning}[!] Skipping copying directory $(basename $src) ${reset}"
    fi
}

# =======================================
#   PROXY CERTS SETUP
# =======================================
proxy_setup() {
    if [ ! -f ${ca_cert} ]; then
        # If ca.crt is absent then all the old signed certs have to be wiped clean first
        if [ -d ${certs_folder} ]; then
            rm -r ${certs_folder}
        fi
        mkdir -p ${certs_folder}

        # A file is created which consists of CA password
        if [ -f ${ca_pass_file} ]; then
            rm ${ca_pass_file}
        fi
        echo $ca_key_pass >> $ca_pass_file
        openssl genrsa -des3 -passout pass:${ca_key_pass} -out "$ca_key" 4096
        openssl req -new -x509 -days 3650 -subj "/C=US/ST=Pwnland/L=OWASP/O=OWTF/CN=MiTMProxy" -passin pass:${ca_key_pass} \
            -key "$ca_key" -out "$ca_cert"
        echo "${warning}[!] Don't forget to add the $ca_cert as a trusted CA in your browser${reset}"
    else
        echo "${info}[*] '${ca_cert}' already exists. Nothing done."
    fi
}

# =======================================
#   DATABASE setup
# =======================================

get_postgres_server_ip() {
    echo "$(sudo netstat -lptn | grep "^tcp " | grep postgres | sed 's/\s\+/ /g' | cut -d ' ' -f4 | cut -d ':' -f1)"
}
get_postgres_server_port() {
    echo "$(sudo netstat -lptn | grep "^tcp " | grep postgres | sed 's/\s\+/ /g' | cut -d ' ' -f4 | cut -d ':' -f2)"
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
  sudo su - postgres -c "psql -l | grep -w $db_name | grep -w $db_user | wc -l"
}

write_db_settings() {
    # Store the password in the .owtf directory
    db_file="$OWTF_DIR/db.yaml"
    if [ -f $db_file ]; then
        rm $db_file
    fi
cat << EOF | tee -ai $db_file
username: "${db_user}"
password: "${db_pass}"
database_name: "${db_name}"
database_ip: "${postgres_server_ip}"
database_port: "${postgres_server_port}"
EOF
}

db_setup() {
    sleep 10
    if [ -z "$DOCKER" ]; then
        write_db_settings
        if [ "$action" = "init" ]; then
            psql postgres -c "CREATE USER $db_user WITH PASSWORD '$db_pass'"
            psql postgres -c "CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;"
            #sudo su postgres -c "psql -c \"CREATE USER $db_user WITH PASSWORD '$db_pass'\""
            #sudo su postgres -c "psql -c \"CREATE DATABASE $db_name WITH OWNER $db_user ENCODING 'utf-8' TEMPLATE template0;\""
        elif [ "$action" = "clean" ]; then
            psql postgres -c "DROP DATABASE $db_name"
            psql postgres -c "DROP USER $db_user"
            sudo su postgres -c "psql -c \"DROP DATABASE $db_name\""
            sudo su postgres -c "psql -c \"DROP USER $db_user\""
        fi

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
    fi
}


# ======================================
#   KALI install
# ======================================
kali_install() {
    echo "${info}[*] Install Kali linux specific dependencies...${reset}"
    make install-dependencies
    echo "${info}[*] Installing required tools...${reset}"
    make opt-tools
    make web-tools
    sh "$SCRIPT_DIR/kali/install.sh"
}

# ======================================
#   SETUP WEB INTERFACE DEPENDENCIES
# ======================================

ui_setup() {
    # Download community written templates for export report functionality.
    if [ ! -d "${ROOT_DIR}/webui/src/Report/templates" ]; then
        echo "${warning} Templates not found, fetching the latest ones...${reset}"
        git clone https://github.com/owtf/templates.git "$ROOT_DIR/webui/src/Report/templates"
    fi

    if [ ! -d ${NVM_DIR} ]; then
        # Instead of using apt-get to install npm we will nvm to install npm because apt-get installs older-version of node
        echo "${normal}[*] Installing npm using nvm.${reset}"
        wget https://raw.githubusercontent.com/creationix/nvm/v0.31.1/install.sh -O /tmp/install_nvm.sh
        bash /tmp/install_nvm.sh
        rm -rf /tmp/install_nvm.sh
    fi

    # Setup nvm and install node
    . ${NVM_DIR}/nvm.sh
    echo "${normal}[*] Installing NPM...${reset}"
    nvm install node
    nvm alias default node
    echo "${normal}[*] npm successfully installed.${reset}"

    # Installing webpack and gulp globally so that it can used by command line to build the bundle.
    npm install -g yarn
    # Installing node dependencies
    echo "${normal}[*] Installing node dependencies.${reset}"
    TMP_DIR=${PWD}
    cd ${ROOT_DIR}/webui
    yarn --silent
    echo "${normal}[*] Yarn dependencies successfully installed.${reset}"

    # Building the ReactJS project
    echo "${normal}[*] Building using webpack.${reset}"
    yarn build &> /dev/null
    echo "${normal}[*] Build successful${reset}"
    cd ${TMP_DIR}
}

#========================================
cat << EOF
 _____ _ _ _ _____ _____
|     | | | |_   _|   __|
|  |  | | | | | | |   __|
|_____|_____| |_| |__|

        @owtfp
    http://owtf.org
EOF

echo "${info}[*] Thanks for installing OWTF! ${reset}"
echo "${info}[!] There will be lot of output, please be patient :)${reset}"

# Copy all necessary directories
for dir in ${ROOT_DIR}/data/*; do
    copy_dirs "$dir" "${OWTF_DIR}/$(basename $OWTF_DIR/$dir)"
done

if [ ! "$(uname)" == "Darwin" ]; then
    check_sudo
fi

proxy_setup

db_setup

ui_setup

if [ "$(check_debian)" == "1" ]; then
    kali_install
fi

make post-install

echo "${info}[*] Finished!${reset}"
echo "${info}[*] Start OWTF by running cd path/to/pentest/directory; python -m owtf${reset}"
