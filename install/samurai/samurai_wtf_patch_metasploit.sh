#!/usr/bin/env sh
#
# Description:
#       Script to fix the MetaSploit install on Samurai by removing default ruby-bundler

# bring in the color variables: `normal`, `info`, `warning`, `danger`, `reset`
. "$(dirname "$(readlink -f "$0")")/../colors.sh"

echo "${info}[*] Removing current package ruby-bundler to avoid conflict with MetaSploit-Framework..${reset}"
sudo -E apt-get -y remove ruby-bundler
echo "${normal}[*] Done!${reset}"
