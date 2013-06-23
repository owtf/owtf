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
echo "\n[*] Running the master install script for OWASP Offensive Web Testing Framework"

# It is easier to work from the root folder of OWTF
cd ../

echo "\n[*] Install restricted tools? [y/n]"
read a
if [ "$a" = "y" ]; then
    cd tools
    echo "$(pwd)"
    "$(pwd)/kali_install.sh"
    cd ../
fi

echo "\n[*] Install restricted dictionaries? [y/n]"
read a
if [ "$a" = "y" ]; then
    cd dictionaries
    echo "$(pwd)"
    "$(pwd)/install_dicts.sh"
    cd ../
    echo "\n[*] Moving cms-explorer to tools folder"
    cp -r dictionaries/cms-explorer tools/restricted/.
    rm -r dictionaries/cms-explorer
fi

echo "\n[*] Install dependencies? [y/n]"
read a
if [ "$a" = "y" ]; then
    cd install
    echo "$(pwd)"
    "$(pwd)/install_dependencies.sh"
    cd ../
fi

echo "\n[*] Create local CA for OWTF Inbound Proxy? [y/n]"
read a
if [ "$a" = "y" ]; then
    mkdir -p ~/.owtf/proxy/certs
    echo "-----------------------------------------------"
    echo "[*] Please use \"owtf\" as password for the key"
    echo "-----------------------------------------------"
    openssl genrsa -des3 -out ~/.owtf/proxy/ca.key 1024
    openssl req -new -x509 -days 3650 -key ~/.owtf/proxy/ca.key -out ~/.owtf/proxy/ca.crt
    echo "\n[*] Donot forget to add the ~/.owtf/proxy/ca.crt as a trusted CA in your browser"
fi

echo "\n[*] Installation script ended"
