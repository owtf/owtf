#!/usr/bin/env python
"""
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
