#!/usr/bin/env sh
#
# owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
# Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
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
get_config_value(){
    
    parameter=$1
    file=$2
    
    echo "$(grep -i $parameter $file | sed  "s|$parameter: ||g;s|~|$HOME|g")"
}

echo "\n[*] Running the master install script for OWASP Offensive Web Testing Framework"

# It is easier to work from the root folder of OWTF
WD=`dirname $0`
cd $WD/../

echo "\n[*] Install restricted tools? [Y/n]"
read a
if [ "$a" != "n" ]; then
    cd tools
    echo "$(pwd)"
    "$(pwd)/kali_install.sh"
    cd ../
fi

echo "\n[*] Install restricted dictionaries? [Y/n]"
read a
if [ "$a" != "n" ]; then
    cd dictionaries
    echo "$(pwd)"
    "$(pwd)/install_dicts.sh"
    cd ../
    echo "\n[*] Moving cms-explorer to tools folder"
    cp -r dictionaries/cms-explorer tools/restricted/.
    rm -r dictionaries/cms-explorer
fi

echo "\n[*] Install dependencies? [Y/n]"
read a
if [ "$a" != "n" ]; then
    cd install
    echo "$(pwd)"
    "$(pwd)/install_dependencies.sh"
    cd ../
fi

echo "\n[*] Install openvas? [Y/n]"
read a
if [ "$a" != "n" ]; then
cd install
    echo "$(pwd)"
    "$(pwd)/install_openvas.sh"
    cd ../
fi
echo "\n[*] Create local CA for OWTF Inbound Proxy? [Y/n]"
read a
if [ "$a" != "n" ]; then
    config_file="$(pwd)/profiles/general/default.cfg"
    certs_folder=$(get_config_value CERTS_FOLDER $config_file)
    ca_cert=$(get_config_value CA_CERT $config_file)
    ca_key=$(get_config_value CA_KEY $config_file)
    if [ ! -d $certs_folder ]; then
        mkdir -p $certs_folder
    fi
    if [ ! -f $ca_cert ]; then
        echo "-----------------------------------------------"
        echo "[*] Please use \"owtf\" as password for the key"
        echo "-----------------------------------------------"
        openssl genrsa -des3 -out "$ca_key" 1024
        openssl req -new -x509 -days 3650 -key "$ca_key" -out "$ca_cert"
        echo "\n[*] Donot forget to add the $ca_cert as a trusted CA in your browser"
    fi
fi

echo "\n[*] Installation script ended"
