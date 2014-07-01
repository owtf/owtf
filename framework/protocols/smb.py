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

Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome
the limitations of set-automate.
"""

import time
import pexpect
import os

from collections import defaultdict
from framework.shell import pexpect_shell
from framework.lib.general import *


class SMB(pexpect_shell.PExpectShell):
    def __init__(self, core):
        # Calling parent class to do its init part.
        pexpect_shell.PExpectShell.__init__(self, core)
        self.CommandTimeOffset = 'SMBCommand'
        self.Mounted = False

    def IsMounted(self):
        return self.Mounted

    def SetMounted(self, value):
        self.Mounted = value

    def check_mount_point_existence(self, options):
        if not os.path.exists(options['SMB_MOUNT_POINT']):
            self.Core.makedirs(options['SMB_MOUNT_POINT'])

    def Mount(self, options, plugin_info):
        if self.IsMounted():
            return True
        cprint("Initialising shell..")
        self.Open(options, plugin_info)
        cprint("Ensuring Mount Point " + options['SMB_MOUNT_POINT'] + " exists..")
        self.check_mount_point_existence(options)
        #self.Core.CreateMissingDirs(options['SMB_MOUNT_POINT'])
        mount_cmd = "smbmount //" + options['SMB_HOST'] + "/" + options['SMB_SHARE'] + " " + options['SMB_MOUNT_POINT']
        if options['SMB_USER']: # Pass user if specified
            mount_cmd += " -o user=" + options['SMB_USER']
        cprint("Mounting share..")
        self.Run(mount_cmd)
        self.Expect("Password:")
        if options['SMB_PASS']: # Pass password if specified
            self.Run(options['SMB_PASS'])
        else:
            self.Run("")  # Send blank line
        self.Expect("#")
        self.SetMounted(True)

    def Transfer(self):
        operation = False
        if self.Options['SMB_DOWNLOAD']:
            self.Download(self.Options['SMB_MOUNT_POINT'] + "/" + self.Options['SMB_DOWNLOAD'], ".")
            operation = True
        if self.Options['SMB_UPLOAD']:
            self.Upload(self.Options['SMB_UPLOAD'], self.Options['SMB_MOUNT_POINT'])
            operation = True
        if not operation:
            cprint("Nothing to do: no SMB_DOWNLOAD or SMB_UPLOAD specified..")

    def UnMount(self, plugin_info):
        if self.IsMounted():
            self.Core.Shell.shell_exec_monitor("umount " + self.Options['SMB_MOUNT_POINT'])
            #self.Run("umount " + self.Options['SMB_MOUNT_POINT'])
            #self.Expect("#")
            self.SetMounted(False)
            self.Close(plugin_info)

    def Upload(self, file_path, mount_point):
        cprint("Copying '" + file_path + "' to '" + mount_point + "'")
        self.Core.Shell.shell_exec_monitor("cp -r " + file_path + " " + mount_point)
        #self.Run("cp -r " + file_path + " " + mount_point)
        #self.Expect("#")

    def Download(self, remote_file_path, target_dir):
        cprint("Copying '" + remote_file_path + "' to '" + target_dir + "'")
        self.Core.Shell.shell_exec_monitor("cp -r " + remote_file_path + " " + target_dir)
        #self.Run("cp -r " + remote_file_path + " " + target_dir)
        #self.Expect("#")
