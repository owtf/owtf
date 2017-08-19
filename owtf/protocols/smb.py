#!/usr/bin/env python
"""
Description:
This is the handler for the Social Engineering Toolkit (SET) trying to overcome
the limitations of set-automate.
"""

import os

from owtf.shell import pexpect_shell
from owtf.lib.general import *
from owtf.utils import FileOperations


class SMB(pexpect_shell.PExpectShell):

    COMPONENT_NAME = "smb"

    def __init__(self):
        self.register_in_service_locator()
        # Calling parent class to do its init part.
        pexpect_shell.PExpectShell.__init__(self)
        self.CommandTimeOffset = 'SMBCommand'
        self.Mounted = False

    def IsMounted(self):
        return self.Mounted

    def SetMounted(self, value):
        self.Mounted = value

    def check_mount_point_existence(self, options):
        if not os.path.exists(options['SMB_MOUNT_POINT']):
            FileOperations.make_dirs(options['SMB_MOUNT_POINT'])

    def Mount(self, options, plugin_info):
        if self.IsMounted():
            return True
        cprint("Initialising shell..")
        self.Open(options, plugin_info)
        cprint("Ensuring Mount Point %s exists..." % options['SMB_MOUNT_POINT'])
        self.check_mount_point_existence(options)
        mount_cmd = "smbmount //%s/%s %s" % (options['SMB_HOST'], options['SMB_SHARE'], options['SMB_MOUNT_POINT'])
        if options['SMB_USER']:  # Pass user if specified.
            mount_cmd += " -o user=%s" % options['SMB_USER']
        cprint("Mounting share..")
        self.Run(mount_cmd, plugin_info)
        self.Expect("Password:")
        if options['SMB_PASS']:  # Pass password if specified.
            self.Run(options['SMB_PASS'], plugin_info)
        else:
            self.Run("", plugin_info)  # Send blank line.
        self.Expect("#")
        self.SetMounted(True)

    def Transfer(self):
        operation = False
        if self.Options['SMB_DOWNLOAD']:
            self.Download("%s/%s" % (self.Options['SMB_MOUNT_POINT'], self.Options['SMB_DOWNLOAD']), ".")
            operation = True
        if self.Options['SMB_UPLOAD']:
            self.Upload(
                self.Options['SMB_UPLOAD'],
                self.Options['SMB_MOUNT_POINT'])
            operation = True
        if not operation:
            cprint("Nothing to do: no SMB_DOWNLOAD or SMB_UPLOAD specified..")

    def UnMount(self, plugin_info):
        if self.IsMounted():
            self.shell_exec_monitor("umount %s" % self.Options['SMB_MOUNT_POINT'])
            self.SetMounted(False)
            self.Close(plugin_info)

    def Upload(self, file_path, mount_point):
        cprint("Copying %s to %s" % (file_path, mount_point))
        self.shell_exec_monitor("cp -r %s %s" % (file_path, mount_point))

    def Download(self, remote_file_path, target_dir):
        cprint("Copying %s to %s" % (remote_file_path, target_dir))
        self.shell_exec_monitor("cp -r %s %s" % (remote_file_path, target_dir))
