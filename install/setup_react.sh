#!/usr/bin/env sh
#
# This script install the node dependencies listed in package.json and build the bundle file using webpack.

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`
. "$(dirname "$(readlink -f "$0")")/utils.sh"

# Instead of using apt-get to install npm we will nvm to install npm because apt-get installs older-version of node
echo "${normal}[*] Installing npm using nvm.${reset}"
wget https://raw.githubusercontent.com/creationix/nvm/v0.31.1/install.sh -O /tmp/install_nvm.sh
bash /tmp/install_nvm.sh
rm -rf /tmp/install_nvm.sh
nvm install node
nvm alias default node
source ~/.bashrc
echo "${normal}[*] npm successfully Installed.${reset}"

# Installing webpack globally so that it can used by command line to build the bundle.
npm install -g webpack

# Installing node dependencies
echo "${normal}[*] Installing node dependencies.${reset}"
npm install
echo "${normal}[*] Dependencies successfully Installed.${reset}"

# Bulding the ReactJS project
echo "${normal}[*] Building using webpack.${reset}"
webpack
echo "${normal}[*] Buld successful${reset}"
