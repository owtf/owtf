"""
owtf.protocols.smb
~~~~~~~~~~~~~~~~~~
This is the handler for the Social Engineering Toolkit (SET) trying to overcome
the limitations of set-automate.
"""
import logging
import os

from owtf.db.session import get_scoped_session
from owtf.shell import pexpect_sh
from owtf.utils.file import FileOperations

__all__ = ["smb"]


class SMB(pexpect_sh.PExpectShell):

    def __init__(self):
        # Calling parent class to do its init part.
        pexpect_sh.PExpectShell.__init__(self)
        self.session = get_scoped_session()
        self.command_time_offset = "SMBCommand"
        self.mounted = False

    def is_mounted(self):
        return self.mounted

    def set_mounted(self, value):
        self.mounted = value

    def check_mount_point_existence(self, options):
        if not os.path.exists(options["SMB_MOUNT_POINT"]):
            FileOperations.make_dirs(options["SMB_MOUNT_POINT"])

    def mount(self, options, plugin_info):
        if self.is_mounted():
            return True
        logging.info("Initialising shell..")
        self.open(options, plugin_info)
        logging.info("Ensuring Mount Point %s exists...", options["SMB_MOUNT_POINT"])
        self.check_mount_point_existence(options)
        mount_cmd = "smbmount //{}/{} {}".format(options["SMB_HOST"], options["SMB_SHARE"], options["SMB_MOUNT_POINT"])
        if options["SMB_USER"]:  # Pass user if specified.
            mount_cmd += " -o user={}".format(options["SMB_USER"])
        logging.info("Mounting share..")
        self.run(mount_cmd, plugin_info)
        self.expect("Password:")
        if options["SMB_PASS"]:  # Pass password if specified.
            self.run(options["SMB_PASS"], plugin_info)
        else:
            self.run("", plugin_info)  # Send blank line.
        self.expect("#")
        self.set_mounted(True)

    def transfer(self):
        operation = False
        if self.options["SMB_DOWNLOAD"]:
            self.download("{}/{}".format(self.options["SMB_MOUNT_POINT"], self.options["SMB_DOWNLOAD"]), ".")
            operation = True
        if self.options["SMB_UPLOAD"]:
            self.upload(self.options["SMB_UPLOAD"], self.options["SMB_MOUNT_POINT"])
            operation = True
        if not operation:
            logging.info("Nothing to do: no SMB_DOWNLOAD or SMB_UPLOAD specified..")

    def unmount(self, plugin_info):
        if self.is_mounted():
            self.shell_exec_monitor(
                session=self.session, command="umount %s".format(self.options["SMB_MOUNT_POINT"]), plugin_info=dict()
            )
            self.set_mounted(False)
            self.close(plugin_info)

    def upload(self, file_path, mount_point):
        logging.info("Copying %s to %s", file_path, mount_point)
        self.shell_exec_monitor(
            session=self.session, command="cp -r {} {}".format(file_path, mount_point), plugin_info=dict()
        )

    def download(self, remote_file_path, target_dir):
        logging.info("Copying %s to %s", remote_file_path, target_dir)
        self.shell_exec_monitor(
            session=self.session, command="cp -r {} {}".format(remote_file_path, target_dir), plugin_info=dict()
        )


smb = SMB()
