"""
owtf.install.install
~~~~~~~~~~~~~~~~~~~~

The main install script
"""

import os
import sys
import logging
import shutil

try:
    import configparser as parser
except ImportError:
    import ConfigParser as parser
from distutils import dir_util

from owtf.utils import FileOperations


def create_directory(directory):
    """Create parent directories as necessary.
    :param directory: (~str) Path of directory to be made.
    :return: True - if directory is created, and False - if not.
    """
    try:
        os.makedirs(directory)
        return True
    except OSError:
        # Checks if the folder is empty
        if not os.listdir(directory):
            return True
        return False

def run_command(command):
    """Execute the provided shell command.
    :param command: (~str) Linux shell command.
    :return: True - if command executed, and False if not.
    """
    logging.info("[*] Running following command")
    logging.info("%s" % command)
    return os.system(command)


def check_sudo():
    """Checks if the user has sudo access.

    :return: Returns true if the user has sudo access
    :rtype: `bool`
    """
    sudo = os.system("sudo -v")
    if not sudo:
        return True
    else:
        logging.warn("[!] Your user does not have sudo privileges. Some OWTF components require"
                          "sudo permissions to install")
        sys.exit(-1)


def install_in_directory(directory, command):
    """Execute a certain command while staying inside one directory.
    :param directory: (~str) Path of directory in which installation command has to be executed.
    :param command: (~str) Linux shell command (most likely `wget` here)
    :return: True - if installation successful or directory already exists, and False if not.
    """
    if create_directory(directory):
        logging.info("[*] Switching to %s" % directory)
        os.chdir(directory)
        return run_command(command)
    else:
        logging.warn("[!] Directory %s already exists, so skipping installation for this" % directory)
        return True


def install_restricted_from_cfg(config_file):
    """Install restricted tools and dependencies which are distro independent.

    :param config_file: Path to configuration file having information about restricted content.
    """
    cp = parser.ConfigParser({"RootDir": root_dir, "Pid": pid})
    cp.read(config_file)
    for section in cp.sections():
        logging.info("[*] Installing %s" % section)
        install_in_directory(os.path.expanduser(cp.get(section, "directory")), cp.get(section, "command"))


def is_debian_derivative():
    """Checks if this is a Debian like linux distribution

    :return: `
    :rtype: `bool`
    """
    compatible_value = os.system("which apt-get >> /dev/null 2>&1")
    if (compatible_value >> 8) == 1:
        return False
    else:
        return True


def copy_dirs(root, dir):
    """Copy directories with error handling to ~/.owtf

    :param src: directory to copy
    :type src: `str`
    :return: None
    :rtype: None
    """

    dest_root = os.path.join(os.path.expanduser('~'), '.owtf')
    target_src_dir = os.path.join(root, 'data', dir)
    target_dest_dir = os.path.join(dest_root, dir)
    # check if already exists
    if not os.path.exists(target_dest_dir):
        shutil.copytree(target_src_dir, target_dest_dir)


if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    pid = os.getpid()

    # Path to custom scripts for tasks such as setting up/ running PostgreSQL db, run arachni, nikto, wapiti etc.
    scripts_path = os.path.join(root_dir, "scripts")

    # Copy all necessary directories
    copy_dirs(root_dir, 'conf')
    copy_dirs(root_dir, 'tools')
    copy_dirs(root_dir, 'dictionaries')

    # Restricted tools and dictionaries
    restricted_cfg = os.path.join(root_dir, "install", "install.cfg")
    print("[*] Great that you are installing OWTF :D")
    print("[!] There will be lot of output, please be patient")
    if not sys.platform == 'darwin':
        check_sudo()
    install_restricted_from_cfg(restricted_cfg)
    print("[*] Finished!")
    print("[*] Start OWTF by running 'cd path/to/pentest/directory; python -m owtf'")

