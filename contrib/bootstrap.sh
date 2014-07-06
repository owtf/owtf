#!/bin/bash
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2014, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# * Neither the name of the <organization> nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# define some constants for simplicity
dev=https://github.com/owtf/owtf/archive/lions_2014.zip
stable=https://github.com/owtf/owtf/archive/v0.45.0_Winter_Blizzard.tar.gz
git=https://github.com/owtf/owtf.git

# warnings in different color
print_warning() {
  T_COLS=`tput cols`
  echo -e "$(tput bold)$(tput setaf 3)$1$(tput sgr0)\n" | fold -sw $(( $T_COLS - 1 ))
}

# invoking the main install script and adding the hoppy fix by @_7a
Install() {
  cd install/; python2 install.py
}

print_warning "[*] OWTF requires minimum of 60 MiB space for a minimal installation (only dictionaries), please make sure you have enough space on your partition."
print_warning "[*] Make sure you have git installed"
echo "[*] Select your OWTF version: "

OPTIONS=("OWTF 0.45.0 Winter Blizzard (stable)" "OWTF Winter Blizzard (git)" "OWTF GSoC'14-dev" "Quit")
select opt in "${OPTIONS[@]}"
do
    case $opt in
        "OWTF 0.45.0 Winter Blizzard (stable)")
            print_warning "[*] Fetching repository and starting installation process"
            print_warning "[*] Make sure you have sudo access."
            wget --no-check-certificate $stable; tar xvf $(basename $stable); rm -f $(basename $stable) 2> /dev/null
            mv owtf-0.45.0_Winter_Blizzard owtf/; cd owtf/
            Install
            ;;
        "OWTF Winter Blizzard (git)")
            print_warning "[*] Fetching repository and starting installation process"
            print_warning "[*] Make sure you have sudo access."
            git clone $git; cd owtf/
            Install
            ;;
        "OWTF GSoC'14-dev")
            print_warning "[*] Fetching repository and starting installation process"
            print_warning "[*] Make sure you have sudo access."
            wget --no-check-certificate $dev; unzip $(basename $dev); rm -f $(basename $dev) 2> /dev/null
            mv owtf-lions_2014/ owtf/; cd owtf/
            Install
            ;;
        "Quit")
            break
            ;;
        *) echo invalid option;;
    esac
done
