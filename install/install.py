#!/usr/bin/env python
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
import os
import sys
import time
import platform
import argparse
from datetime import datetime

import ConfigParser


class Installer(object):
    """
    This class takes care of installation of various restricted stuff across various linux distros
    """
    def __init__(self, RootDir):
        self.RootDir = RootDir
        self.pid = os.getpid()
        self.owtf_pip = os.path.join(RootDir, "install", "owtf.pip") # OWTF python libraries
        self.restricted_cfg = os.path.join(RootDir, "install", "distro-independent.cfg") # Restricted tools and dictionaries which are distro independent
        self.distros_cfg = os.path.join(RootDir, "install", "linux-distributions.cfg") # Various distros and install scripts
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--no-user-input', help='run script with default options for user input', action="store_true") 
        self.parser.add_argument('--core-only', help='install only owtf dependencies, skip optional tools', action="store_true")

    def create_directory(self, directory):
        # Create parent directories as necessary
        try:
            os.makedirs(directory)
            return True
        except OSError:
            return False

    def run_command(self, command):
        print("[*] Running following command")
        print("%s"%(command))
        os.system(command)

    def install_in_directory(self, directory, command):
        if self.create_directory(directory):
            print("[*] Switching to %s"%(directory))
            os.chdir(directory)
            self.run_command(command)
        else:
            print("[!] Directory %s already exists, so skipping installation for this"%(directory))

    def install_using_pip(self, requirements_file):
        # Instead of using file directly with pip which can crash because of single library
        self.run_command("sudo -E pip2 install --upgrade -r %s"%(requirements_file))

    def install_restricted_from_cfg(self, config_file):
        cp = ConfigParser.ConfigParser({"RootDir":self.RootDir, "Pid":self.pid})
        cp.read(config_file)
        for section in cp.sections():
            print("[*] Installing %s"%(section))
            self.install_in_directory(os.path.expanduser(cp.get(section, "directory")), cp.get(section, "command"))

    def install(self, cmd_arguments):

        args = self.parser.parse_args(cmd_arguments)

        # User asked to select distro (in case it cannot be automatically detected) and distro related stuff is installed
        cp = ConfigParser.ConfigParser({"RootDir":self.RootDir, "Pid":self.pid})
        cp.read(self.distros_cfg)

        #Try get the distro automatically
        distro, version, arch = platform.linux_distribution()
        distro_num = 0
        if "kali" in distro.lower():
            distro_num = 1
        elif "samurai" in distro.lower():
            distro_num = 2

        # Loop until proper input is received
        while True:
            if distro_num != 0:
                print("[*] %s has been automatically detected... Continuing in auto-mode"%(distro))
                break

            if args.no_user_input:
                distro_num = 0
                break

            print("")
            for i in range(0, len(cp.sections())):
                print("(%d) %s"%(i+1, cp.sections()[i]))
            print("(0) %s (%s)"%("My distro is not listed :(", distro))
            distro_num = raw_input("Select a number based on your distribution : ")
            try: # Cheking if valid input is received
                distro_num = int(distro_num)
                break
            except ValueError:
                print('')
                print("Please enter a valid number")
                continue

        if distro_num != 0:
            self.run_command(cp.get(cp.sections()[int(distro_num)-1], "install"))
        else:
            print("Skipping distro related installation :(")

        # First all distro independent stuff is installed
        self.install_restricted_from_cfg(self.restricted_cfg)

        if args.core_only == True:
            return

        print("Upgrading pip to the latest version ...")
        # Upgrade pip before install required libraries
        self.run_command("sudo pip2 install --upgrade pip")

        if args.no_user_input:
            fixsetuptools = 'y'
        else:
            # ask the user if they really want to delete the symlink
            fixsetuptools = raw_input("Delete /usr/lib/python2.7/dist-packages/setuptools.egg-info? (y/n)\n(recommended, solves some issues)")

        if fixsetuptools == 'y':
            # backup the original symlink
            print("Backing up the original symlink...")
            ts = time.time()
            human_timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H:%M:%S')

            # backup the original symlink
            self.run_command("mv /usr/lib/python2.7/dist-packages/setuptools.egg-info /usr/lib/python2.7/dist-packages/setuptools.egg-info" + "-BACKUP-" + human_timestamp)

            print("The original symlink exists at /usr/lib/python2.7/dist-packages/setuptools.egg-info-BACKUP-" + human_timestamp)

            # Finally owtf python libraries installed using pip
            self.install_using_pip(self.owtf_pip)

        else:
            print("Moving on with the installation but you were warned: there may be some errors!")
            # Finally owtf python libraries installed using pip
            self.install_using_pip(self.owtf_pip)

if __name__ == "__main__":
    print("[*] Great that you are installing OWTF :D")
    print("[!] There will be lot of output, please be patient")
    RootDir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    installer = Installer(RootDir)
    installer.install(sys.argv[1:])
    print("[*] Finished")
