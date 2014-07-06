#!/usr/bin/env python2
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
# _author_  = Viyat Bhalodia
# This module is a part of Google Summer of Code 2014, OWASP OWTF
# Description:
#    + Make the current proxy implementation session-aware
#    + Ability to detect login/logout sequences
#    + Replay login sequence if session expires or user logged out
#
import simplejson as json
import os
import sys
import re
from lxml import html
from tornado.web import RequestHandler

# Define constants here,later document them to user profiles
LOGIN_TRIES      = 5
LOGIN_RETRY_WAIT = 5


class SessionHandler(object):

    def __init__(self, core):
       # initialize Core to access all variables
       self.Core = core

    def GetSessionsDir(self):
        """
        Creates the missing dir for sessions
        """
        session_dir = self.Core.Config.RootDir + "/" + self.Core.Config.GetOutputDirForTargets() + "/http_sessions"
        self.Core.CreateMissingDir(session_dir)

        return session_dir

    def read(self):
        """
        Reads current session info
        """
        try:
            session_file = os.path.join(self.GetSessionsDir, 'index')
            with self.Core.open(session_file, owtf_clean=False) as session:
                return json.load(session)
        except IOError, e:
            print e, "cannot read from file"
            exit()

    def write(self, data):
        """
        Writes the json data to the session_file
        """
        with self.Core.open(os.path.join(self.GetSessionsDir, 'index'), 'w') as outfile:
              json.dump(data, outfile)

    def update_tokens(self, tokens):
        with self.Core.open(os.path.join(self.GetSessionsDir, 'index'), "r+") as sessionfile:
            data = json.load(sessionfile)

            for key in data["tokens"]:
                for token in tokens:

            sessionfile.seek(0)  # rewind
            sessionfile.write(json.dumps(data))
        # still incomplete;


class AuthenticationHandler(object):

    def __init__(self, Core)
        self.Core = Core

    def get_config(self):
        return self.Core.DB.Config.Get("AUTO_LOGIN")

    def set_autologin(self):
        self.Core.DB.Config.Update("AUTO_LOGIN", "True")

    def unset_autologin(self):
        self.Core.DB.Config.Update("AUTO_LOGIN", "False")

    def login_sequence(self, string=None):
        pattern = '^.' + string + '.$'
        try:
            login_seq = re.compile(self.Core.DB.Config.Get('LOGIN_SEQUENCE'))
        except AttributeError:
            login_seq = re.compile(pattern)

        return login_seq

    def logout_sequence(self, string=None):
        pattern = '^.' + string + '.$'
        try:
            logout_seq = re.compile(self.Core.DB.Config.Get('LOGOUT_SEQUENCE')
        except AttributeError:
            logout_seq = re.compile(pattern)

        return logout_seq


class FormsParser(object):

    def __init__(self, response):
        self.response = response
        RequestHandler.__init__(self, response)

    def login_form(self):
        """ Parses the response body to collect forms """

        # get DOM
        dom = lxml.html.parse(self.response.body).getroot()
        # parse the dom to find form; specifically the login form

        #for form in dom.forms:
