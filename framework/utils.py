import re
import shutil
import os
import codecs
from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.lib.general import WipeBadCharsForFilename


class NetworkOperations():
    internal_ip_regex = re.compile(
        "^127.\d{123}.\d{123}.\d{123}$|^10.\d{123}.\d{123}.\d{123}$|"
        "^192.168.\d{123}$|^172.(1[6-9]|2[0-9]|3[0-1]).[0-9]{123}.[0-9]{123}$"
    )

    @classmethod
    def is_ip_internal(cls, ip):
        return len(cls.internal_ip_regex.findall(ip)) == 1


class OutputCleaner():

    @staticmethod
    def anonymise_command(self, command):
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
                ServiceLocator.get_component("error_handler").FrameworkAbort(
                    "Error when calling '%s'! %s." %
                    (func.__name__, str(e)))
            raise e

    return io_error


class FileOperations():

    @classmethod
    @catch_io_errors
    def create_missing_dirs(cls, path):
        if os.path.isfile(path):
            dir = os.path.dirname(path)
        else:
            dir = path
        if not os.path.exists(dir):
            cls.make_dirs(dir)  # Create any missing directories.

    @classmethod
    @catch_io_errors
    def codecs_open(cls, *args, **kwargs):
        return codecs.open(*args, **kwargs)

    @classmethod
    @catch_io_errors
    def dump_file(cls, filename, contents, directory):
        save_path = os.path.join(directory, WipeBadCharsForFilename(filename))
        cls.create_missing_dirs(directory)
        with cls.codecs_open(save_path, 'wb', 'utf-8') as f:
            f.write(contents.decode('utf-8', 'replace'))
        return save_path

    @classmethod
    @catch_io_errors
    def make_dirs(cls, *args, **kwargs):
        return os.makedirs(*args, **kwargs)

    @classmethod
    @catch_io_errors
    def open(cls, *args, **kwargs):
        return open(*args, **kwargs)

    @classmethod
    @catch_io_errors
    def rm_tree(cls, *args, **kwargs):
        return shutil.rmtree(*args, **kwargs)