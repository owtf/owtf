#!/usr/bin/env python
"""
Declare the helper functions for the framework.
"""

from __future__ import absolute_import, print_function
from collections import defaultdict
import os
import re
import base64
import errno


def cprint(msg):
    pad = "[-] "
    print(pad + str(msg).replace("\n", "\n" + pad))
    return Message


def MultipleReplace(Text, ReplaceDict):
    """
    Perform multiple replacements in one go using the replace dictionary
    in format: { 'search' : 'replace' }
    """
    NewText = Text
    for Search, Replace in ReplaceDict.items():
        NewText = NewText.replace(Search, str(Replace))
    return NewText


def check_pid(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
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


def WipeBadCharsForFilename(Filename):
    return MultipleReplace(Filename, {'(': '', ' ': '_', ')': '', '/': '_'})


def RemoveListBlanks(src):
    return [el for el in src if el]


def List2DictKeys(List):
    Dictionary = defaultdict(list)
    for Item in List:
        Dictionary[Item] = ''
    return Dictionary


def add_to_dict(from_dict, to_dict):
    for k, v in from_dict.items():
        if hasattr(v, 'copy') and callable(getattr(v, 'copy')):
            to_dict[k] = v.copy()
        else:
            to_dict[k] = v


def merge_dicts(a, b):
    """
    Returns a by-value copy contained the merged content of the 2 passed
    dictionaries
    """
    new_dict = defaultdict(list)
    add_to_dict(a, new_dict)
    add_to_dict(b, new_dict)
    return new_dict


def truncate_lines(str, num_lines, EOL="\n"):
    retur EOL.join(str.split(EOL)[0:num_lines])


def derive_http_method(method, data):  # Derives the HTTP method from Data, etc
    d_method = method
    # Method not provided: Determine method from params
    if d_method is None or d_method == '':
        d_method = 'GET'
        if data != '' and data is not None:
            d_method = 'POST'
    return d_method


def get_random_str(len):
    """function returns random strings of length len"""
    return base64.urlsafe_b64encode(os.urandom(len))[0:len]


def scrub_output(output):
    """remove all ANSI control sequences from the output"""
    ansi_escape = re.compile(r'\x1b[^m]*m')
    return ansi_escape.sub('', output)


def get_file_as_list(filename):
    try:
        with open(filename, 'r') as File:
            Output = File.read().split("\n")
            cprint("Loaded file: %s" % filename)
    except IOError:
        log("Cannot open file: %s (%s)" % (filename, str(sys.exc_info())))
        Output = []
    return Output


def paths_exist(PathList):
    ValidPaths = True
    for Path in PathList:
        if Path and not os.path.exists(Path):
            log("WARNING: The path %s does not exist!" % Path)
            ValidPaths = False
    return ValidPaths
