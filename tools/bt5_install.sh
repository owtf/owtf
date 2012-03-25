#!/usr/bin/env bash
#
# Description: Installation script for tools not in Backtrack or unreliable in Backtrack
# (i.e. Backtrack chose the development version instead of the stable one)
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
# * Neither the name of the copyright owner nor the
# names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# This script needs to be run to download tools with potentially restrictive licensing (cannot be redistributed)
INSTALL_DIR="$(dirname $0)/restricted"
mkdir -p $INSTALL_DIR
(
    cd $INSTALL_DIR
    # NOTE: Arachni v0.4 is still a bit unstable, it's best to stick with Arachni v0.3 in the meantime
    #TOOL_DIR="arachni-v0.4.0.2-cde"
    TOOL_DIR="arachni-v0.3-cde"
    TGZ_FILE="$TOOL_DIR.tar.gz"
    mkdir -p $TOOL_DIR
    (
        cd $TOOL_DIR
        if [ ! -f $TGZ_FILE ]; then
            wget https://github.com/Zapotek/arachni/downloads/$TGZ_FILE
            tar xvfz $TGZ_FILE
            rm -f $TGZ_FILE
        fi
    )

    TOOL_DIR="whatweb"
    mkdir -p $TOOL_DIR
    (
    cd $TOOL_DIR
    TOOL_NAME="whatweb-0.4.7.tar.gz"
    if [ ! -f $TOOL_NAME ]; then
        echo "Getting whatweb .."
        wget http://www.morningstarsecurity.com/downloads/$TOOL_NAME
        tar xvfz *
        rm -f $TOOL_NAME
    fi
    )

    echo "Getting websecurify .."
    TOOL_DIR="websecurify"
    mkdir -p $TOOL_DIR
    (
    cd $TOOL_DIR
    wget http://websecurify.googlecode.com/files/Websecurify%20Scanner%200.9.tgz
    tar xvfz *
    rm -f Websecurify\ Scanner\ 0.9.tgz
    )

    echo "Getting wpscan.."
    TOOL_DIR="wpscan"
    mkdir -p $TOOL_DIR
    (
    cd $TOOL_DIR
    svn checkout http://wpscan.googlecode.com/svn/trunk/ ./wpscan-1.1
    )

    TOOL_DIR="dos/http"
    mkdir -p $TOOL_DIR
    (
    cd $TOOL_DIR
    TOOL_NAME="slowloris.pl"
    if [ ! -f $TOOL_NAME ]; then
        echo "Getting slowloris .."
        wget http://ha.ckers.org/slowloris/$TOOL_NAME
        chmod 700 $TOOL_NAME
    fi
    )

    TOOL_DIR="decoding/cookies"
    mkdir -p $TOOL_DIR
    (
    cd $TOOL_DIR
    if [ ! -f BIG-IP_cookie_decoder.py ]; then
        echo "Getting BIG-IP_cookie_decoder .."
        wget http://www.taddong.com/tools/BIG-IP_cookie_decoder.zip
        unzip BIG-IP_cookie_decoder.zip
        rm -f BIG-IP_cookie_decoder.zip
    fi
    )
)
