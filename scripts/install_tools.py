#!/usr/bin/env python

from __future__ import print_function
from future.utils import iteritems

import os

import yaml

import yamlordereddictloader

BLUE = "\033[94m"
GREEN = "\033[92m"
WARNING = "\033[93m"
FAIL = "\033[91m"
RESET = "\033[0m"

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
OWTF_CONF = os.path.join(os.path.expanduser("~"), ".owtf")

with open(os.path.join(CURR_DIR, "tools.yaml"), "r") as f:
    conf = yaml.load(f, Loader=yamlordereddictloader.Loader)


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


def install_in_directory(directory, command):
    """Execute a certain command while staying inside one directory.
    :param directory: (~str) Path of directory in which installation command has to be executed.
    :param command: (~str) Linux shell command (most likely `wget` here)
    :return: True - if installation successful or directory already exists, and False if not.
    """
    if create_directory(directory):
        print(BLUE + "[*] Switching to {}".format(directory) + RESET)
        os.chdir(directory)
        os.system(command)
    else:
        print(WARNING + "[!] Directory {} already exists, so skipping installation for this".format(directory) + RESET)


def parse_and_install():
    for k, v in iteritems(conf):
        cmd = v["command"]
        directory = os.path.join(OWTF_CONF, v["directory"])
        print(BLUE + "[*] Running {0} in {1}".format(cmd, directory) + RESET)
        install_in_directory(directory, cmd)


if __name__ == "__main__":
    parse_and_install()
