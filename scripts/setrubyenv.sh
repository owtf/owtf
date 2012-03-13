#!/usr/bin/env bash
#
# Description:
# Some tools (whatweb and others) require ruby 1.8 and others (i.e. BeEF) require ruby 1.9.2
# This script allows you to quickly change from ruby 1.8 to 1.9.2 and viceversa
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

# TODO: replace Ruby 1.9.2 with 1.9.3

SCRIPT=`basename $0`

if [ $# -ne 1 ]; then
    cat <<-EOF
	Usage: $SCRIPT <ruby_version: 1.8, 1.9.2>

	Examples:
	  - Set ruby 1.8: $SCRIPT 1.8
	  - Set ruby 1.9.2: $SCRIPT 1.9.2
EOF
    exit
fi

VERSION=$1
echo "* Switching to Ruby $VERSION..."

OPTION="1"
if [ $VERSION == '1.9.2' ]; then
    OPTION="2"
fi

# Export version gem paths
export GEM_PATH=/var/lib/gems/$VERSION/gems
export GEM_HOME=/var/lib/gems/$VERSION/gems

# Pick ruby version
(sleep 2 ; echo $OPTION) | update-alternatives --config ruby

if [ -z $? ] ; then
    echo "* Successfully switched to Ruby $VERSION."
else
    echo "* Could not switch to Ruby $VERSION."
fi
