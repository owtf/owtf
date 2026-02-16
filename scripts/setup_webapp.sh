#!/bin/sh
# Set script and root directory variables
SCRIPT_DIR="$(pwd -P)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")/owtf"
# Set NVM directory
export NVM_DIR="${HOME}/.nvm"
bold=$(tput bold)
reset=$(tput sgr0)
danger=${bold}$(tput setaf 1)   # red
warning=${bold}$(tput setaf 3)  # yellow
info=${bold}$(tput setaf 6)     # cyan
normal=${bold}$(tput setaf 7)   # white
# ======================================
#   SETUP WEB INTERFACE DEPENDENCIES
# ======================================
ui_setup() {
    # Download community written templates for export report functionality
    if [ ! -d "${ROOT_DIR}/webapp/src/containers/Report/templates" ]; then
        echo "${warning}Templates not found, fetching the latest ones...${reset}"
        git clone https://github.com/owtf/templates.git "$ROOT_DIR/webapp/src/containers/Report/templates"
    fi
    # Install NVM if not already installed
    if [ ! -d "${NVM_DIR}" ]; then
        echo "${normal}[*] Installing npm using nvm.${reset}"
        wget https://raw.githubusercontent.com/creationix/nvm/v0.31.1/install.sh -O /tmp/install_nvm.sh
        bash /tmp/install_nvm.sh
        rm -rf /tmp/install_nvm.sh
    fi
    # Source NVM script and install Node.js and npm
    . "${NVM_DIR}/nvm.sh"
    echo "${normal}[*] Installing NPM...${reset}"
    nvm install 18.0
    nvm alias default node
    echo "${normal}[*] npm successfully installed.${reset}"
    # Install yarn globally and project dependencies
    npm install -g yarn
    echo "${normal}[*] Installing node dependencies.${reset}"
    cd "${ROOT_DIR}/webapp"
    yarn --silent
    echo "${normal}[*] Yarn dependencies successfully installed.${reset}"
    echo "${normal}[*] Building webapp using Vite.${reset}"
    yarn build &> /dev/null
    echo "${normal}[*] Build successful${reset}"
}
# Function to install Nginx
install_nginx() {
    echo "${info}[*] Installing Nginx...${reset}"
    sudo apt-get install -y nginx
    echo "${info}[*] Nginx successfully installed.${reset}"
}
# Function to check if build files exist and return a boolean
check_build_files() {
    if [ -d "${ROOT_DIR}/webapp/build" ] && [ -f "${ROOT_DIR}/webapp/build/index.html" ]; then
        return 0  # true
    else
        return 1  # false
    fi
}
# Function to copy build files to Nginx directory
copy_build_files() {
    echo "${info}[*] Copying build files....${reset}"
    if [ ! -d "/usr/share/nginx/owtf" ]; then
        sudo mkdir /usr/share/nginx/owtf
    fi
    if check_build_files; then
        sudo cp -r "${ROOT_DIR}/webapp/build/"* /usr/share/nginx/owtf
        echo "${info}[*] Build files successfully copied to /usr/share/nginx/owtf${reset}"
    else
        echo "${warning}[!] Build files not found. Please build the webapp first.${reset}"
        ui_setup
    fi
}
# Function to copy Nginx configuration file
copy_nginx_config() {
    echo "${info}[*] Copying Nginx configuration file...${reset}"
    if [ -f "/etc/nginx/sites-enabled/owtf.conf" ]; then
        sudo rm /etc/nginx/sites-enabled/owtf.conf
    fi
    if [ -f "/etc/nginx/sites-available/owtf.conf" ]; then
        sudo rm /etc/nginx/sites-available/owtf.conf
    fi
    sudo cp "${ROOT_DIR}/webapp/owtf.conf" /etc/nginx/sites-available/owtf.conf
    sudo ln -s /etc/nginx/sites-available/owtf.conf /etc/nginx/sites-enabled/owtf.conf
    sudo systemctl restart nginx
    echo "${info}[*] Nginx configuration file successfully copied.${reset}"
}
# Main script execution
install_nginx
copy_build_files
copy_nginx_config
