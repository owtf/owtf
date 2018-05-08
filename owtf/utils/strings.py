"""
owtf.utils.strings
~~~~~~~~~~~~~~~~~~

"""
import base64
import binascii
import logging
import os
import re
from collections import defaultdict
import six

from owtf.settings import REPLACEMENT_DELIMITER

search_regex = re.compile("{!s}([a-zA-Z0-9-_]*?){!s}".format(REPLACEMENT_DELIMITER, REPLACEMENT_DELIMITER))


def utf8(string):
    if isinstance(string, six.string_types):
        return string.encode("utf8")
    return string


def to_str(byte):
    if isinstance(byte, bytes):
        return byte.decode("utf-8", "ignore")
    return byte


def str2bool(string):
    """ Converts a string to a boolean

    :param string: String to convert
    :type string: `str`
    :return: Boolean equivalent
    :rtype: `bool`
    """
    return not (string in ["False", "false", 0, "0"])


def multi_replace(text, replace_dict):
    """Recursive multiple replacement function
    :param text: Text to replace
    :type text: `str`
    :param replace_dict: The parameter dict to be replaced with
    :type replace_dict: `dict`
    :return: The modified text after replacement
    :rtype: `str`
    """
    new_text = text
    for key in search_regex.findall(new_text):
        # Check if key exists in the replace dict ;)
        if replace_dict.get(key, None):
            # A recursive call to remove all level occurrences of place
            # holders.
            new_text = new_text.replace(
                REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER, multi_replace(replace_dict[key], replace_dict)
            )
    new_text = os.path.expanduser(new_text)
    return new_text


def get_as_list(key_list):
    """Get values for keys in a list

    :param key_list: List of keys
    :type key_list: `list`
    :return: List of corresponding values
    :rtype: `list`
    """
    from owtf.config import config_handler

    value_list = []
    for key in key_list:
        value_list.append(config_handler.get_val(key))
    return value_list


def get_header_list(key):
    """Get list from a string of values for a key

    :param key: Key
    :type key: `str`
    :return: List of values
    :rtype: `list`
    """
    from owtf.config import config_handler

    return config_handler.get_val(key).split(",")


def pad_key(key):
    """Add delimiters.

    :param key: Key to pad
    :type key: `str`
    :return: Padded key string
    :rtype: `str`
    """
    return REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER


def strip_key(key):
    """Replaces key with empty space

    :param key: Key to clear
    :type key: `str`
    :return: Empty key
    :rtype: `str`
    """
    return key.replace(REPLACEMENT_DELIMITER, "")


def multi_replace_dict(text, replace_dict):
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


def wipe_bad_chars(filename):
    """The function wipes bad characters from name of output file

    :param filename: The file name to scrub
    :type filename: `str`
    :return: New replaced file filename
    :rtype: `str`
    """
    return multi_replace(filename, {"(": "", " ": "_", ")": "", "/": "_"})


def remove_blanks_list(src):
    """Removes empty elements from the list

    :param src: List
    :type src: `list`
    :return: New list without blanks
    :rtype: `list`
    """
    return [el for el in src if el]


def list_to_dict_keys(list):
    """Convert a list to dict with keys from list items

    :param list: list to convert
    :type list: `list`
    :return: The newly formed dictionary
    :rtype: `dict`
    """
    dictionary = defaultdict(list)
    for item in list:
        dictionary[item] = ""
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
        if hasattr(v, "copy") and callable(getattr(v, "copy")):
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


def truncate_lines(str, num_lines, eol="\n"):
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
    return eol.join(str.split(eol)[0:num_lines])


def get_random_str(len):
    """Function returns random strings of length len

    :param len: Length
    :type len: `int`
    :return: Random generated string
    :rtype: `str`
    """
    return base64.urlsafe_b64encode(os.urandom(len))[0:len]


def gen_secure_random_str():
    return binascii.hexlify(os.urandom(32))


def scrub_output(output):
    """Remove all ANSI control sequences from the output

    :param output: Output to scrub
    :type output: `str`
    :return: Scrubbed output
    :rtype: `str`
    """
    ansi_escape = re.compile(r"\x1b[^m]*m")
    return ansi_escape.sub("", output)


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
            logging.log("WARNING: The path %s does not exist!", path)
            valid = False
    return valid


def is_convertable(value, conv):
    """Convert a value

    :param value:
    :type value:
    :param conv:
    :type conv:
    :return:
    :rtype:
    """
    try:
        return conv(value)
    except ValueError:
        return None


def str_to_dict(string):
    """Convert a string to a dict

    :param string: String to convert
    :type string: `str`
    :return: Resultant dict
    :rtype: `dict`
    """
    dict = defaultdict(list)
    count = 0
    prev_item = ""
    for item in string.strip().split("="):
        if count % 2 == 1:  # Key.
            dict[prev_item] = item
        else:  # Value.
            dict[item] = ""
            prev_item = item
        count += 1
    return dict
