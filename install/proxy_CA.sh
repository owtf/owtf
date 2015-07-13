#!/usr/bin/env sh
#
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
RootDir=$1

get_config_value(){
    
    parameter=$1
    file=$2
    
    echo "$(grep -i $parameter $file | sed  "s|$parameter: ||g;s|~|$HOME|g")"
}

config_file="$RootDir/profiles/general/default.cfg"
certs_folder=$(get_config_value CERTS_FOLDER $config_file)
ca_cert=$(get_config_value CA_CERT $config_file)
ca_key=$(get_config_value CA_KEY $config_file)
ca_pass_file=$(get_config_value CA_PASS_FILE $config_file)
ca_key_pass=$(head /dev/random -c16 | od -tx1 -w16 | head -n1 | cut -d' ' -f2- | tr -d ' ')

if [ ! -f $ca_cert ]; then

    # If ca.crt is absent then all the old signed certs have to be wiped clean first
    if [ -d $certs_folder ]; then
        rm -r $certs_folder
    fi
    mkdir -p $certs_folder

    # A file is created which consists of CA password
    if [ -f $ca_pass_file ]; then
        rm $ca_pass_file
    fi
    echo $ca_key_pass >> $ca_pass_file

    openssl genrsa -des3 -passout pass:$ca_key_pass -out "$ca_key" 1024
    openssl req -new -x509 -days 3650 -subj "/C=US/ST=Pwnland/L=OWASP/O=OWTF/CN=MiTMProxy" -passin pass:$ca_key_pass -key "$ca_key" -out "$ca_cert"
    echo "[*] Don't forget to add the $ca_cert as a trusted CA in your browser"
fi
