#!/usr/bin/env python

import os
import sys
import time
import platform
import argparse
from datetime import datetime
from space_checker_utils import wget_wrapper

import ConfigParser


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
    Colorizer.normal("[*] Running following command")
    Colorizer.info("%s" % command)
    # If command is `wget`, then before execution, `wget_wrapper` checks whether there is enough disk space available
    if not wget_wrapper(command):
        return False
    return os.system(command)


def owtf_last_commit():
    """Prints the local git repo's last commit hash."""
    if os.path.exists(os.path.join(root_dir, '.git')):
        command = 'git log -n 1 --pretty=format:"%H"'
        commit_hash = os.popen(command).read()
        return commit_hash
    else:
        return "*Not a git repository.*"


def check_sudo():
    """Checks if the user has sudo access."""
    sudo = os.system("sudo -v")
    if not sudo:
        return
    else:
        Colorizer.warning("[!] Your user does not have sudo privileges. Some OWTF components require sudo permissions to install")
        sys.exit()


def install_in_directory(directory, command):
    """Execute a certain command while staying inside one directory.

    :param directory: (~str) Path of directory in which installation command has to be executed.
    :param command: (~str) Linux shell command (most likely `wget` here)

    :return: True - if installation successful or directory already exists, and False if not.
    """
    if create_directory(directory):
        Colorizer.info("[*] Switching to %s" % directory)
        os.chdir(directory)
        return run_command(command)
    else:
        Colorizer.warning("[!] Directory %s already exists, so skipping installation for this" % directory)
        return True


def install_using_pip(requirements_file):
    """Install pip libraries as mentioned in a requirements file.

    :param requirements_file: (~str) Path to requirements file - in which libraries are listed.

    :return: True - if installation successful, and False if not.
    """
    # Instead of using file directly with pip which can crash because of single library
    return run_command("sudo -E pip2 install --upgrade -r %s" % requirements_file)


def install_restricted_from_cfg(config_file):
    """Install restricted tools and dependencies which are distro independent.

    :param config_file: (~str) Path to configuration file having information about restricted content.
    """
    cp = ConfigParser.ConfigParser({"RootDir": root_dir, "Pid": pid})
    cp.read(config_file)
    for section in cp.sections():
        Colorizer.info("[*] Installing %s" % section)
        install_in_directory(os.path.expanduser(cp.get(section, "directory")), cp.get(section, "command"))


def is_compatible():
        compatible_value = os.system("which apt-get >> /dev/null 2>&1")
        if compatible_value>>8 == 1:
            return False
        else:
            return True

def finish(error_code):
        if error_code == 1:
            Colorizer.danger("\n[!] The installation was not successful.")
            Colorizer.normal("[*] Visit https://github.com/owtf/owtf for help ")
        else:
            Colorizer.success("[*] Finished!")
            Colorizer.info("[*] Start OWTF by running './owtf.py' in parent directory")


def install(cmd_arguments):
    """Perform installation of OWTF Framework. Wraps around all helper methods made in this module.

    :param cmd_arguments:
    """
    args = parser.parse_args(cmd_arguments)
    # User asked to select distro (in case it can't be automatically detected) and distro related stuff is installed
    cp = ConfigParser.ConfigParser({"RootDir": root_dir, "Pid": pid})
    cp.read(distros_cfg)

    # Try get the distro automatically
    distro, version, arch = platform.linux_distribution()
    distro_num = 0
    if "kali" in distro.lower():
        distro_num = 1
    elif "samurai" in distro.lower():
        distro_num = 2
    elif is_compatible():
    	distro_num = 3

    # Loop until proper input is received
    while True:
        if distro_num != 0:
            Colorizer.info("[*] %s has been automatically detected... " % distro)
            Colorizer.normal("[*] Continuing in auto-mode")
            break

        if args.no_user_input:
            distro_num = 0
            break

        print("")
        for i, item in enumerate(cp.sections()):
            Colorizer.warning("(%d) %s" % (i + 1, item))
        Colorizer.warning("(0) My distro is not listed :( %s" % distro)

        distro_num = raw_input("Select a number based on your distribution : ")
        try:
            # Checking if valid input is received
            distro_num = int(distro_num)
            break
        except ValueError:
            print('')
            Colorizer.warning("[!] Invalid Number specified")
            continue

    # First all distro independent stuff is installed
    install_restricted_from_cfg(restricted_cfg)
    if distro_num != 0:
        run_command(cp.get(cp.sections()[int(distro_num)-1], "install"))
    else:
        Colorizer.normal("[*] Skipping distro related installation :(")

    # Return if option to install only owtf dependencies is given, as there are optional tools further
    if args.core_only:
        return

    Colorizer.normal("[*] Upgrading pip to the latest version ...")
    # Upgrade pip before install required libraries
    run_command("sudo pip2 install --upgrade pip")
    Colorizer.normal("Upgrading setuptools to the latest version ...")
    # Upgrade setuptools
    run_command("sudo pip2 install --upgrade setuptools")
    Colorizer.normal("Upgrading cffi to the latest version ...")
    # Mitigate cffi errors by upgrading it first
    run_command("sudo pip2 install --upgrade cffi")

    if distro_num == '1':
        # check kali major release number 0.x, 1.x, 2.x
        kali_version = os.popen("cat /etc/issue", "r").read().split(" ")[2][0]
        if kali_version == '1':
            if args.no_user_input:
                fixsetuptools = 'n'
            else:
                fixsetuptools = raw_input("Delete /usr/lib/python2.7/dist-packages/setuptools.egg-info? (y/n)\n(recommended, solves some issues in Kali 1.xx)")

            if fixsetuptools == 'y':
                Colorizer.normal("[*] Backing up the original symlink...")
                ts = time.time()
                human_timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H:%M:%S')

                symlink_orig_path = "/usr/lib/python2.7/dist-packages/setuptools.egg-info"
                run_command("mv %s %s-BACKUP-%s" % (symlink_orig_path, symlink_orig_path, human_timestamp))
                Colorizer.info("[*] The original symlink exists at %s-BACKUP-%s" % (symlink_orig_path, human_timestamp))

                install_using_pip(owtf_pip)
        else:
            Colorizer.warning("[!] Moving on with the installation but you were warned: there may be some errors!")

    install_using_pip(owtf_pip)

    run_command("sudo sh %s init" % (os.path.join(scripts_path, "db_setup.sh")))
    run_command("sudo sh %s" % (os.path.join(scripts_path, "db_run.sh")))


class Colorizer:

    """Helper class for colorized strings.

    Different statements will have different colors:

        - `normal`, denoting ongoing procedure (WHITE)
        - `info`, any file path, commit hash or any other info (BLUE)
        - `warning`, any potential hindrance in installation (YELLOW)
        - `danger`, abrupt failure, desired file/dir not found etc. (RED)
    """

    BOLD = '\033[1m'
    RED = BOLD + '\033[91m'
    GREEN = BOLD + '\033[92m'
    YELLOW = BOLD + '\033[93m'
    BLUE = BOLD + '\033[34m'
    PURPLE = BOLD + '\033[95m'
    CYAN = BOLD + '\033[36m'
    WHITE = BOLD + '\033[37m'
    END = '\033[0m\033[0m'

    def __init__(self):
        pass

    @classmethod
    def normal(cls, string):
        print(cls.WHITE + string + cls.END)

    @classmethod
    def info(cls, string):
        print(cls.CYAN + string + cls.END)

    @classmethod
    def warning(cls, string):
        print(cls.YELLOW + string + cls.END)

    @classmethod
    def success(cls, string):
        print(cls.GREEN + string + cls.END)

    @classmethod
    def danger(cls, string):
        print(cls.RED + string + cls.END)


if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    pid = os.getpid()

    # Path to custom scripts for tasks such as setting up/ running PostgreSQL db, run arachni, nikto, wapiti etc.
    scripts_path = os.path.join(root_dir, "scripts")

    # OWTF python libraries
    owtf_pip = os.path.join(root_dir, "install", "owtf.pip")

    # Restricted tools and dictionaries which are distro independent
    restricted_cfg = os.path.join(root_dir, "install", "distro-independent.cfg")

    # Various distros and install scripts
    distros_cfg = os.path.join(root_dir, "install", "linux-distributions.cfg")

    parser = argparse.ArgumentParser()
    parser.add_argument('--no-user-input', help='run script with default options for user input', action="store_true")
    parser.add_argument('--core-only', help='install only owtf dependencies, skip optional tools', action="store_true")

    Colorizer.normal("[*] Great that you are installing OWTF :D")
    Colorizer.warning("[!] There will be lot of output, please be patient")

    Colorizer.info("[*] Last commit hash: %s" % owtf_last_commit())
    check_sudo()
    installer_status_code = install(sys.argv[1:])

    finish(installer_status_code)