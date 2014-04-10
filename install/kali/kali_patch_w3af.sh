#!/usr/bin/env sh
#
# Description:
#       Script to fix the license request made by w3af when run for first time
#
# Date:    2013-06-04
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

# Install missing stuff needed for w3af in kali
sudo apt-get install python2.7-dev libsqlite3-dev
sudo pip install pybloomfiltermmap==0.3.11 # The 0.3.12 pypi package is broken
sudo pip install clamd PyGithub GitPython esmre nltk pdfminer futures guess-language cluster msgpack-python python-ntlm
sudo pip install git+git://github.com/ramen/phply.git\#egg=phply
sudo pip install xdot

if [ -f ~/.w3af/startup.conf ]
then
    if ! grep -i "^accepted-disclaimer = true$" ~/.w3af/startup.conf
    then
        echo "accepted-disclaimer = true" >> ~/.w3af/startup.conf
    fi
else
    if [ ! -d ~/.w3af ]
    then
        mkdir ~/.w3af
    fi
    echo "[STARTUP_CONFIG]" >> ~/.w3af/startup.conf
    echo "auto-update = true" >> ~/.w3af/startup.conf
    echo "frequency = D" >> ~/.w3af/startup.conf
    echo "accepted-disclaimer = true" >> ~/.w3af/startup.conf
fi
