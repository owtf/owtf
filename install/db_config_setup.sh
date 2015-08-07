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
# This script creates a default config file at user specified location if it
# doesn't already exist
# Usage : $0 [rootdir] [--cfg-only]
# @param --cfg-only : Create the db.cfg file and skip postgres server setup and start

get_config_value(){

    parameter=$1
    file=$2

    echo "$(grep -i $parameter $file | sed  "s|$parameter: ||g;s|~|$HOME|g")"
}

# Simple command line argument handler.
cfg_only=false

for arg in "$@"
do
    if [ "$arg" == "--cfg-only" ]; then
        cfg_only=true
    else
        RootDir=$arg
    fi
done

FILE_PATH=$(readlink -f "$0")
INSTALL_DIR=$(dirname "$FILE_PATH")
RootDir=${RootDir:-$(dirname "$INSTALL_DIR")}

config_file="$RootDir/framework/config/framework_config.cfg"
db_config_file="$(get_config_value DATABASE_SETTINGS_FILE $config_file)"

db_name="owtfdb"
db_user="owtf_db_user"
db_pass=$(head /dev/random -c8 | od -tx1 -w16 | head -n1 | cut -d' ' -f2- | tr -d ' ')

if [ ! -f $db_config_file ]; then
    mkdir -p "$(dirname $db_config_file)"
    echo "[*] Creating default config at $db_config_file"
    echo "[*] Don't forget to edit $db_config_file"
    echo "
# Want to create a postgres role and db. Follow steps carefully:
# + Edit this file with proper ip and port settings (No need to change if using defaults)
# + Run the db_setup.sh in scripts folder to setup a new user and new db as mentioned in this file
DATABASE_IP: 127.0.0.1
# Default postgres listens on 5432
DATABASE_PORT: 5432
DATABASE_NAME: $db_name
DATABASE_USER: $db_user
DATABASE_PASS: $db_pass" >> $db_config_file

    if $cfg_only ; then
        exit 0
    fi

    echo "[*] Do you want to create database and user as specified in $db_config_file [Y/n]?"
    read choice
    if [ choice != 'n' ]; then
        $RootDir/scripts/db_run.sh
    fi
fi
