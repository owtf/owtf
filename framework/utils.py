import os
import re
import sys
import shutil
import codecs
import logging
import tempfile
from ipaddr import IPAddress
from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.lib.general import WipeBadCharsForFilename



def is_internal_ip(ip):
    # parses the input IP into IPv4 or IPv6
    parsed_ip = IPAddress(ip)
    return parsed_ip.is_private


class OutputCleaner():

    @staticmethod
    def anonymise_command(command):
        command = command.decode('utf-8', 'ignore')
        target = ServiceLocator.get_component("target")
        # Host name setting value for all targets in scope.
        for host in target.GetAll('HOST_NAME'):
            if host:  # Value is not blank
                command = command.replace(host, 'some.target.com')
        for ip in target.GetAll('HOST_IP'):
            if ip:
                command = command.replace(ip, 'xxx.xxx.xxx.xxx')
        return command


def catch_io_errors(func):
    """Decorator on I/O functions.

    If an error is detected, force OWTF to quit properly.

    """
    def io_error(*args, **kwargs):
        """Call the original function while checking for errors.

        If `owtf_clean` parameter is not explicitely passed or if it is
        set to `True`, it force OWTF to properly exit.

        """
        owtf_clean = kwargs.pop('owtf_clean', True)
        try:
            return func(*args, **kwargs)
        except (OSError, IOError) as e:
            if owtf_clean:
                error_handler = ServiceLocator.get_component("error_handler")
                if error_handler:
                    error_handler.FrameworkAbort( "Error when calling '%s'! %s." % (func.__name__, str(e)))
            raise e
    return io_error


def directory_access(path, mode):
    """Check if a directory can be accessed in the specified mode by the current user.

    :param str path: Directory path.
    :param str mode: Access type.

    :return: Valid access rights
    :rtype:`str`
    """

    try:
        temp_file = tempfile.NamedTemporaryFile(mode=mode, dir=path, delete=True)
    except (IOError, OSError):
        return False
    return True


def print_version(root_dir, commit_hash=False, version=False):
    # check if the root dir is a git repository
    if os.path.exists(os.path.join(root_dir, '.git')):
        command = ('git log -n 1 --pretty=format:"%H"')
        commit_hash = os.popen(command).read()

    if commit_hash and version:
        return "OWTF Version: %s, Release: %s  \n" % (
                ServiceLocator.get_component("config").FrameworkConfigGet('VERSION'),
                ServiceLocator.get_component("config").FrameworkConfigGet('RELEASE'))+ \
                "Last commit hash: " + commit_hash
    elif commit_hash:
        return commit_hash
    elif version:
        return "OWTF Version: %s, Release: %s " % (
                ServiceLocator.get_component("config").FrameworkConfigGet('VERSION'),
                ServiceLocator.get_component("config").FrameworkConfigGet('RELEASE'))
    else:
        pass

class FileOperations(object):

    @staticmethod
    @catch_io_errors
    def create_missing_dirs(path):
        # truncate filepath to 255 char (*nix limit)
        # See issue #521
        directory = path[:255]
        if os.path.isfile(directory):
            directory = os.path.dirname(directory)
        if not os.path.exists(directory):
            # Create any missing directories.
            FileOperations.make_dirs(directory)

    @staticmethod
    @catch_io_errors
    def codecs_open(*args, **kwargs):
        return codecs.open(*args, **kwargs)

    @staticmethod
    @catch_io_errors
    def dump_file(filename, contents, directory):
        save_path = os.path.join(directory, WipeBadCharsForFilename(filename))
        FileOperations.create_missing_dirs(directory)
        with FileOperations.codecs_open(save_path, 'wb', 'utf-8') as f:
            f.write(contents.decode('utf-8', 'replace'))
        return save_path

    @staticmethod
    @catch_io_errors
    def make_dirs(*args, **kwargs):
        return os.makedirs(*args, **kwargs)

    @staticmethod
    @catch_io_errors
    def open(*args, **kwargs):
        return open(*args, **kwargs)

    @staticmethod
    @catch_io_errors
    def rm_tree(*args, **kwargs):
        return shutil.rmtree(*args, **kwargs)

    @staticmethod
    @catch_io_errors
    def mkdir(*args, **kwargs):
        return os.mkdir(*args, **kwargs)


class OWTFLogger():

    @staticmethod
    def log(msg, *args, **kwargs):
        logging.info(msg, *args, **kwargs)
