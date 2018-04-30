"""
owtf.utils.file
~~~~~~~~~~~~~~~

"""
import codecs
import logging
import os
import shutil
import sys
import tempfile

from owtf.settings import LOGS_DIR, OUTPUT_PATH, OWTF_CONF, TARGETS_DIR, WORKER_LOG_DIR
from owtf.utils.error import abort_framework
from owtf.utils.strings import wipe_bad_chars


def catch_io_errors(func):
    """Decorator on I/O functions.
    If an error is detected, force OWTF to quit properly.
    """

    def io_error(*args, **kwargs):
        """Call the original function while checking for errors.
        If `owtf_clean` parameter is not explicitely passed or if it is
        set to `True`, it force OWTF to properly exit.
        """
        owtf_clean = kwargs.pop("owtf_clean", True)
        try:
            return func(*args, **kwargs)
        except (OSError, IOError) as e:
            if owtf_clean:
                abort_framework("Error when calling '{!s}'! {!s}.".format(func.__name__, str(e)))
            raise e

    return io_error


class FileOperations(object):

    @staticmethod
    @catch_io_errors
    def create_missing_dirs(path):
        """Creates missing directories if not already present

        :param path: Path of the directory to create
        :type path: `str`
        :return:
        :rtype: None
        """
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
        """ A wrapper for Python codes with additional argument support"""
        return codecs.open(*args, **kwargs)

    @staticmethod
    @catch_io_errors
    def dump_file(filename, contents, directory):
        """Create a file with user supplied contents

        :param filename: File to be created
        :type filename: `str`
        :param contents: Contents to write to the file
        :type contents: `str`
        :param directory: Directory where the file will be saved
        :type directory: `str`
        :return: The final full path of the created file
        :rtype: `str`
        """
        save_path = os.path.join(directory, wipe_bad_chars(filename))
        FileOperations.create_missing_dirs(directory)
        with FileOperations.codecs_open(save_path, "w", "utf-8") as f:
            f.write(contents)
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


def directory_access(path, mode):
    """Check if a directory can be accessed in the specified mode by the current user.

    :param str path: Directory path.
    :param str mode: Access type.

    :return: Valid access rights
    :rtype: `str`
    """
    try:
        temp_file = tempfile.NamedTemporaryFile(mode=mode, dir=path, delete=True)
    except (IOError, OSError):
        return False
    return True


def get_file_as_list(filename):
    """Get file contents as a list

    :param filename: File path
    :type filename: `str`
    :return: Output list of the content
    :rtype: `list`
    """
    try:
        with open(filename, "r") as f:
            output = f.read().split("\n")
            logging.info("Loaded file: %s", filename)
    except IOError:
        logging.error("Cannot open file: %s (%s)", filename, str(sys.exc_info()))
        output = []
    return output


def create_temp_storage_dirs(owtf_pid):
    """Create a temporary directory in /tmp with pid suffix.

    :return:
    :rtype: None
    """
    tmp_dir = os.path.join("/tmp", "owtf")
    if not os.path.exists(tmp_dir):
        tmp_dir = os.path.join(tmp_dir, str(owtf_pid))
        if not os.path.exists(tmp_dir):
            FileOperations.make_dirs(tmp_dir)


def clean_temp_storage_dirs(owtf_pid):
    """Rename older temporary directory to avoid any further confusions.

    :return:
    :rtype: None
    """
    curr_tmp_dir = os.path.join("/tmp", "owtf", str(owtf_pid))
    new_tmp_dir = os.path.join("/tmp", "owtf", "old-{!s}".format(owtf_pid))
    if os.path.exists(curr_tmp_dir) and os.access(curr_tmp_dir, os.W_OK):
        os.rename(curr_tmp_dir, new_tmp_dir)


def get_output_dir():
    """Gets the output directory for the session

    :return: The path to the output directory
    :rtype: `str`
    """
    output_dir = os.path.expanduser(OUTPUT_PATH)
    if not os.path.isabs(output_dir) and directory_access(os.getcwd(), "w+"):
        return output_dir
    else:
        # The output_dir may not be created yet, so check its parent.
        if directory_access(os.path.dirname(output_dir), "w+"):
            return output_dir
    return os.path.expanduser(os.path.join(OWTF_CONF, output_dir))


def get_output_dir_target():
    """Returns the output directory for the targets

    :return: Path to output directory
    :rtype: `str`
    """
    return os.path.join(get_output_dir(), TARGETS_DIR)


def get_dir_worker_logs():
    """Returns the output directory for the worker logs

    :return: Path to output directory for the worker logs
    :rtype: `str`
    """
    return os.path.join(get_output_dir(), WORKER_LOG_DIR)


def cleanup_target_dirs(target_url):
    """Cleanup the directories for the specific target

    :return: None
    :rtype: None
    """
    return FileOperations.rm_tree(get_target_dir(target_url))


def get_target_dir(target_url):
    """Gets the specific directory for a target in the target output directory

    :param target_url: Target URL for which directory path is needed
    :type target_url: `str`
    :return: Path to the target URL specific directory
    :rtype: `str`
    """
    clean_target_url = target_url.replace("/", "_").replace(":", "").replace("#", "")
    return os.path.join(get_output_dir_target(), clean_target_url)


def create_output_dir_target(target_url):
    """Creates output directories for the target URL

    :param target_url: The target URL
    :type target_url: `str`
    :return: None
    :rtype: None
    """
    FileOperations.create_missing_dirs(get_target_dir(target_url))


def get_logs_dir():
    """
    Get log directory by checking if abs or relative path is provided in
    config file
    """
    # Check access for logs dir parent directory because logs dir may not be created.
    if os.path.isabs(LOGS_DIR) and directory_access(os.path.dirname(LOGS_DIR), "w+"):
        return LOGS_DIR
    else:
        return os.path.join(get_output_dir(), LOGS_DIR)


def get_log_path(process_name):
    """Get the log file path based on the process name
    :param process_name: Process name
    :type process_name: `str`
    :return: Path to the specific log file
    :rtype: `str`
    """
    log_file_name = "{!s}.log".format(process_name)
    return os.path.join(get_logs_dir(), log_file_name)
