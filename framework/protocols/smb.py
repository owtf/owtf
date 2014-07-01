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
    def __init__(self, Core):
        pexpect_shell.PExpectShell.__init__(self, Core) # Calling parent class to do its init part
        self.CommandTimeOffset = 'SMBCommand'
        self.Mounted = False

    def IsMounted(self):
        return self.Mounted

    def SetMounted(self, Value):
        self.Mounted = Value

    def check_mount_point_existence(self, Options):
        if not os.path.exists(Options['SMB_MOUNT_POINT']):
            self.Core.makedirs(Options['SMB_MOUNT_POINT'])

    def Mount(self, Options, PluginInfo):
        if self.IsMounted():
            return True
        cprint("Initialising shell..")
        self.Open(Options, PluginInfo)
        cprint("Ensuring Mount Point " + Options['SMB_MOUNT_POINT'] + " exists..")
        self.check_mount_point_existence(Options)
        #self.Core.CreateMissingDirs(Options['SMB_MOUNT_POINT'])
        MountCmd = "smbmount //" + Options['SMB_HOST'] + "/" + Options['SMB_SHARE'] + " " + Options['SMB_MOUNT_POINT']
        if Options['SMB_USER']: # Pass user if specified
            MountCmd += " -o user=" + Options['SMB_USER']
        cprint("Mounting share..")
        self.Run(MountCmd)
        self.Expect("Password:")
        if Options['SMB_PASS']: # Pass password if specified
            self.Run(Options['SMB_PASS'])
        else:
            self.Run("")  # Send blank line
        self.Expect("#")
        self.SetMounted(True)

    def Transfer(self):
        Operation = False
        if self.Options['SMB_DOWNLOAD']:
            self.Download(self.Options['SMB_MOUNT_POINT'] + "/" + self.Options['SMB_DOWNLOAD'], ".")
            Operation = True
        if self.Options['SMB_UPLOAD']:
            self.Upload(self.Options['SMB_UPLOAD'], self.Options['SMB_MOUNT_POINT'])
            Operation = True
        if not Operation:
            cprint("Nothing to do: no SMB_DOWNLOAD or SMB_UPLOAD specified..")

    def UnMount(self, PluginInfo):
        if self.IsMounted():
            self.Core.Shell.shell_exec_monitor("umount " + self.Options['SMB_MOUNT_POINT'])
            #self.Run("umount " + self.Options['SMB_MOUNT_POINT'])
            #self.Expect("#")
            self.SetMounted(False)
            self.Close(PluginInfo)

    def Upload(self, FilePath, MountPoint):
        cprint("Copying '" + FilePath + "' to '" + MountPoint + "'")
        self.Core.Shell.shell_exec_monitor("cp -r " + FilePath + " " + MountPoint)
        #self.Run("cp -r " + FilePath + " " + MountPoint)
        #self.Expect("#")

    def Download(self, RemoteFilePath, TargetDir):
        cprint("Copying '" + RemoteFilePath + "' to '" + TargetDir + "'")
        self.Core.Shell.shell_exec_monitor("cp -r " + RemoteFilePath + " " + TargetDir)
        #self.Run("cp -r " + RemoteFilePath + " " + TargetDir)
        #self.Expect("#")
