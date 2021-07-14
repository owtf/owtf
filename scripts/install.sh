#!/usr/bin/env sh

#set -e

SCRIPT_DIR="$(pwd -P)/scripts"
OWTF_DIR="${HOME}/.owtf"
ROOT_DIR="$(dirname $SCRIPT_DIR)/owtf"
CWD="$(dirname $ROOT_DIR)"
os=${OSTYPE//[0-9.-]*/}


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

# =======================================
#   COMMON FUNCTIONS
# =======================================
if [[ "$(cat /proc/1/cgroup 2> /dev/null | grep docker | wc -l)" > 0 ]] || [ -f /.dockerenv ]; then
  IS_DOCKER=1
else
  IS_DOCKER=0
fi

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

check_root() {
	if [ $EUID -eq 0 ]; then
		return 1
	else
		return 0
	fi
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
        echo "${info}[*] '${ca_cert}' already exists. Nothing done.${reset}"
    fi
}

# ======================================
#   SETUP WEB INTERFACE DEPENDENCIES
# ======================================

ui_setup() {
    # Download community written templates for export report functionality.
    if [ ! -d "${ROOT_DIR}/webapp/src/containers/Report/templates" ]; then
        echo "${warning} Templates not found, fetching the latest ones...${reset}"
        git clone https://github.com/owtf/templates.git "$ROOT_DIR/webapp/src/containers/Report/templates"
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
    nvm install 15.0
    nvm alias default node
    echo "${normal}[*] npm successfully installed.${reset}"

    # Installing webpack and gulp globally so that it can used by command line to build the bundle.
    npm install -g yarn
    # Installing node dependencies
    echo "${normal}[*] Installing node dependencies.${reset}"
    TMP_DIR=${PWD}
    cd ${ROOT_DIR}/webapp
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

# Copy git hooks
echo "${info}[*] Installing pre-commit and black for git hooks...${reset}"
pip install pre-commit==1.8.2
pip install black==18.4a3
pre-commit install

# Copy all necessary directories
for dir in ${ROOT_DIR}/data/*; do
    copy_dirs "$dir" "${OWTF_DIR}/$(basename $OWTF_DIR/$dir)"
done

if [ ! "$(uname)" == "Darwin" ]; then
    check_sudo > /dev/null
fi

proxy_setup
ui_setup
make post-install

echo "${info}[*] Finished!${reset}"
echo "${info}[*] Start OWTF by running cd path/to/pentest/directory; owtf${reset}"
echo "${warning}[!] Please add a new JWT_SECRET_KEY in the settings file located in owtf/owtf/settings.py${reset} "
echo "${warning}[!] Please setup SMTP server of your choice in the settings file located in owtf/owtf/settings.py${reset} "
