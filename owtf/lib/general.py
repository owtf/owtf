"""
owtf.lib.general
~~~~~~~~~~~~~~~~

Declare the helper functions for the framework.
"""


from collections import defaultdict
import os
import re
import base64
import errno


def cprint(msg):
    """Wrapper found console print function with padding

    :param msg: Message to print
    :type msg: `str`
    :return: Padded message
    :rtype: `str`
    """
    pad = "[-] "
    print(pad + str(msg).replace("\n", "\n" + pad))
    return msg


def multi_replace(text, replace_dict):
    """Perform multiple replacements in one go using the replace dictionary
    in format: { 'search' : 'replace' }

    :param text: Text to replace
    :type text: `str`
    :param replace_dict: The replacement strings in a dict
    :type replace_dict: `dict`
    :return: `str`
    :rtype:
    """
    new_text = text
    for search, replace in list(replace_dict.items()):
        new_text = new_text.replace(search, str(replace))
    return new_text


def check_pid(pid):
    """Check whether pid exists in the current process table.
    UNIX only.

    :param pid: Pid to check
    :type pid: `int`
    :return: True if pid exists, else false
    :rtype: `bool`
    """
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


def wipe_bad_chars(filename):
    """The function wipes bad characters from name of output file

    :param filename: The file name to scrub
    :type filename: `str`
    :return: New replaced file filename
    :rtype: `str`
    """
    return multi_replace(filename, {'(': '', ' ': '_', ')': '', '/': '_'})


def remove_blanks_list(src):
    """Removes empty elements from the list

    :param src: List
    :type src: `list`
    :return: New list without blanks
    :rtype: `list`
    """
    return [el for el in src if el]


def List2DictKeys(list):
    """Convert a list to dict with keys from list items

    :param list: list to convert
    :type list: `list`
    :return: The newly formed dictionary
    :rtype: `dict`
    """
    dictionary = defaultdict(list)
    for item in list:
        dictionary[item] = ''
    return dictionary


def add_to_dict(from_dict, to_dict):
    """Add the items from dict a with copy attribute to dict b

    :param from_dict: Dict to copy from
    :type from_dict: `dict`
    :param to_dict: Dict to copy to
    :type to_dict: `dict`
    :return: None
    :rtype: None
    """
    for k, v in list(from_dict.items()):
        if hasattr(v, 'copy') and callable(getattr(v, 'copy')):
            to_dict[k] = v.copy()
        else:
            to_dict[k] = v


def merge_dicts(a, b):
    """Returns a by-value copy contained the merged content of the 2 passed
    dictionaries

    :param a: Dict a
    :type a: `dict`
    :param b: Dict b
    :type b: `dict`
    :return: New merge dict
    :rtype: `dict`
    """
    new_dict = defaultdict(list)
    add_to_dict(a, new_dict)
    add_to_dict(b, new_dict)
    return new_dict


def truncate_lines(str, num_lines, EOL="\n"):
    """Truncate and remove EOL characters

    :param str: String to truncate
    :type str: `str`
    :param num_lines: Number of lines to process
    :type num_lines: `int`
    :param EOL: EOL char
    :type EOL: `char`
    :return: Joined string after truncation
    :rtype: `str`
    """
    return EOL.join(str.split(EOL)[0:num_lines])


def derive_http_method(method, data):
    """Derives the HTTP method from Data, etc

    :param method: Method to check
    :type method: `str`
    :param data: Data to check
    :type data: `str`
    :return: Method found
    :rtype: `str`
    """
    d_method = method
    # Method not provided: Determine method from params
    if d_method is None or d_method == '':
        d_method = 'GET'
        if data != '' and data is not None:
            d_method = 'POST'
    return d_method


def get_random_str(len):
    """Function returns random strings of length len

    :param len: Length
    :type len: `int`
    :return: Random generated string
    :rtype: `str`
    """
    return base64.urlsafe_b64encode(os.urandom(len))[0:len]


def scrub_output(output):
    """Remove all ANSI control sequences from the output

    :param output: Output to scrub
    :type output: `str`
    :return: Scrubbed output
    :rtype: `str`
    """
    ansi_escape = re.compile(r'\x1b[^m]*m')
    return ansi_escape.sub('', output)


def get_file_as_list(filename):
    """Get file contents as a list

    :param filename: File path
    :type filename: `str`
    :return: Output list of the content
    :rtype: `list`
    """
    try:
        with open(filename, 'r') as f:
            output = f.read().split("\n")
            cprint("Loaded file: %s" % filename)
    except IOError:
        log("Cannot open file: %s (%s)" % (filename, str(sys.exc_info())))
        output = []
    return output


def paths_exist(path_list):
    """Check if paths in the list exist

    :param path_list: The list of paths to check
    :type path_list: `list`
    :return: True if valid paths, else False
    :rtype: `bool`
    """
    valid = True
    for path in path_list:
        if path and not os.path.exists(path):
            log("WARNING: The path %s does not exist!" % path)
            valid = False
    return valid
