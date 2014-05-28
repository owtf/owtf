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
#
# Usage:
# the basic session mechanism is this:
# * take some data, serialize it, store it somewhere.
# * assign an id to it.
# * put the id in a cookie.
# * when you get a request, load the id and deserialize it.

import simplejson as json
import os.path
import hashlib
import uuid
import tornado.web

from framework.lib.general import cprint


class Session(dict):
    """
    * A Session is basically a dict with a site, state {Active, None}, session_id and session_tokens (dict)
    """
    def __init__(self, site, state, valid=True, session_id, session_tokens=None, urls=None):
        self.site = site
        self.session_id = session_id
        self.state = state # "active" or "expired"
        self.valid = valid
        self.session_tokens = {}  # Session tokens for the site will be stored as "site": [tokens]
        self.urls = []  # Useful later on to map sessions with accessible URLS

    def updateSession(self, state="active", valid=False, session_id):
        return self.session_tokens.pop("expired")

    def removeSession(self, session_id):
        cprint("Removing session...")
        return self.session_tokens = {} and self.state = "expired"


class SessionManager(object):
    """
    * SessionManager handles the cookie and file read/writes for a Session
    """
    def __init__(self, session_dir = ''):

        # figure out where to store the session files
        if session_dir == '':
            session_dir = os.path.join(os.path.dirname(__file__), 'sessions')
        self.session_dir = session_dir

    def read(self, session_id):
        session_path = self._get_session_path(session_id)
        try : 
            data = json.loads(open(session_path))
            if type(data) == type({}):
                return data
            else:
                return {}
        except IOError:
            return {}
        
    def get(self, session_id = None):
        # set up the session state (create it from scratch, or from parameters)
        if session_id == None:
            session_should_exist = False
            session_id = self._generate_uid()
        else:
            session_should_exist = True
            session_id = session_id

        # create the session object
        session = Session(session_id)

        # read the session file, if this is a pre-existing session
        if session_should_exist:
            data = self.read(session_id)
            for i, j in data.iteritems():
                session[i] = j
        
        return session
    
    def get_session_path(self, session_id):
        return os.path.join(self.session_dir, 'SESSION' + str(session_id))

    def set(self, session):
        session_path = self._get_session_path(session.session_id)
        with open(session_path, 'wb') as session_file:
            json.dump(dict(session.items()), session_file)

    def generate_uid(self):
        base = hashlib.md5(str(uuid.uuid4()))
        return base.hexdigest()
