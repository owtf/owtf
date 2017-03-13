#!/usr/bin/env sh
#
# Description:
#       Script to fix the license request made by w3af when run for first time

# Install missing stuff needed for w3af in kali
sudo apt-get -y install python2.7-dev libsqlite3-dev
pip2 install --upgrade clamd PyGithub GitPython pybloomfiltermmap esmre nltk pdfminer futures guess-language cluster msgpack-python python-ntlm
pip2 install --upgrade git+https://github.com/ramen/phply.git\#egg=phply
pip2 install --upgrade xdot

if [ ! -f ~/.w3af/startup.conf ]
then
    # FIrst create a dummy profile because all we need is to show he disclaimer
    echo "exit" > /tmp/w3af_disclaimer_check_owtf.profile
    w3af_console -s /tmp/w3af_disclaimer_check_owtf.profile
fi
