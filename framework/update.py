#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This script helps in updating OWTF.
"""

import os
import json
import urllib2

from subprocess import PIPE
from subprocess import Popen as execute

from framework.lib.general import cprint


class Updater(object):
    """Updater object is used to update OWTF"""

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.git_dir = os.path.join(self.root_dir, ".git")
        self.remote_tags_url = 'https://api.github.com/repos/owtf/owtf/tags'
        self.proxy = None
        self.proxy_auth_username = None
        self.proxy_auth_password = None
        self.process_environ = os.environ
        self.remote_tags = {}

    def set_proxy(self, proxy, proxy_auth=None):
        """Set Proxy method when outbound proxy is provided."""
        self.proxy = proxy  # IP:PORT
        self.proxy_auth = proxy_auth

    def prepare(self):
        """Prepares all urllib2 openers.

        Also prepares env variables when proxy is provided and parses
        local,remote config files & stores them in dictionaries.

        """
        if self.proxy:
            proxy_support = self.proxy
            if self.proxy_auth:
                proxy_support = self.proxy_auth + '@' + proxy_support
            proxy_handler = urllib2.ProxyHandler({
                'http': 'http://' + proxy_support,
                'https': 'https://' + proxy_support})
            opener = urllib2.build_opener(proxy_handler)
            urllib2.install_opener(opener)
            self.process_environ['http_proxy'] = 'http://' + proxy_support
            self.process_environ['https_proxy'] = 'https://' + proxy_support
        # GITHUB API is used to fetch all the tags
        response = urllib2.urlopen(self.remote_tags_url)
        self.remote_tags = json.loads(response.read())

    def check(self):
        """Check whether the repository is a git repo.

        Needed because update process is using git.

        """
        if not os.path.exists(os.path.join(self.root_dir, '.git')):
            cprint(
                "Not a git repository. Please checkout OWTF repo from GitHub "
                "(eg:- git clone https://github.com/owtf/owtf owtf)")
            return False
        else:
            self.prepare()
            return True

    def last_commit_hash(self):
        """Returns the last commit hash in the local repo."""
        command = ("git --git-dir=%s log -n 1 "%(self.git_dir))
        command += "--pretty=format:%H"
        process = execute(
            command,
            shell=True,
            env=self.process_environ,
            stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        commit_hash = stdout.strip()
        return commit_hash

    def update(self):
        if self.check():
            # Instead of checking tag names, commit hashes is checked for
            # foolproof method.
            if self.last_commit_hash() != self.remote_tags[0]["commit"]["sha"]:
                cprint(
                    "Trying to update OWTF to %s" %
                    self.remote_tags[0]["name"])
                command = (
                    "git pull; git reset --soft %s" %
                    self.remote_tags[0]["name"])
                process = execute(
                    command,
                    shell=True,
                    env=self.process_environ,
                    stdout=PIPE, stderr=PIPE)
                stdout, stderr = process.communicate()
                success = not process.returncode
                if success:
                    cprint(
                        "OWTF Successfully Updated to Latest Stable Version!!")
                    cprint("Version Tag: %s" % self.remote_tags[0]["name"])
                    cprint(
                        "Please run install script if you face any errors "
                        "after updating")
                else:
                    cprint("Unable to update :(")
            else:
                cprint(
                    "Seems like you are running latest version => %s" %
                    self.remote_tags[0]["name"])
                cprint("Happy pwning!! :D")
