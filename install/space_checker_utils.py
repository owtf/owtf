from __future__ import division
import re
import os
import subprocess
import urllib2


def byte_to_human(size):
    """Transform the size in bytes into the appropriate unit of measurement.

    :param int size: Size in bytes.

    :return: Actual size in B/KB/MB/GB.
    :rtype: str
    """
    try:
        size = int(size)
    except ValueError:
        return (0, "B")
    um = "B"
    if size < pow(2,20):
        size = size / pow(2,10)
        um = "KB"
    elif size < pow(2,30):
        size = size / pow(2, 20)
        um = "MB"
    else:
        size = size / pow(2, 30)
        um = "GB"

    return (size, um)


def get_wget_download_size(command):
    """Get the whole download size in bytes.

    :param str command: Wget command.

    :return: The actual download size in bytes.
    :rtype: int
    """
    # Wget supports HTTP, HTTPS and FTP protocols.
    if not command.startswith('wget '):
        return 0

    # Check the url(s) is/are valid.
    urls = re.findall(r'((?:https|http|ftp)://[^\s]+)', command)

    if not urls:
        return 0

    size = 0
    for url in urls:
        try:
            response = urllib2.urlopen(url)
            size += int(response.info().getheader('Content-Length'))
        except (urllib2.HTTPError, urllib2.URLError, ValueError, TypeError):
            pass
    return size


def get_fs_free_space():
    """Get the available space of the current filesystem.

    :return: The available size in KB.
    :rtype: int
    """
    try:
        stat = os.statvfs('.')
        return (stat.f_bavail * stat.f_frsize) / 1024
    except  OSError:
        print("[!] Failed to get the filesystem disk space usage")
        return 0


def wget_wrapper(command):
    """Checks if the current filesystem has enough available space in order to proceed downloading data using wget.

    :param str command: The installation command.

    :return: The installation can proceed.
    :rtype: bool
    """
    commands = re.findall('(wget.*?);', command)
    size = sum(get_wget_download_size(wget_command) for wget_command in commands)

    while size / 1024 > get_fs_free_space():
        print("[!] Not enough space to proceed with the download.")
        human_size, um = byte_to_human(size)
        answer = raw_input("[!] Please free %s %s and proceed, or type \'n\' to skip the download. [Y/n] "
                %('{0:.3g}'.format(human_size), um))
        if answer == 'n':
            return False
    return True
