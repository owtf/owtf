#!/usr/bin/env python
"""
Declare the helper functions for the framework.
"""

from collections import defaultdict
from framework.lib.filelock import FileLock
import logging
import multiprocessing
import os
import pprint
import random
import string
import sys
import threading
import time
import base64
import errno


def cprint(Message):
    Pad = "[-] "
    print Pad+str(Message).replace("\n", "\n"+Pad)
    return Message


def MultipleReplace(Text, ReplaceDict):
    """
    Perform multiple replacements in one go using the replace dictionary
    in format: { 'search' : 'replace' }
    """
    NewText = Text
    for Search,Replace in ReplaceDict.items():
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
    return MultipleReplace(Filename, { '(':'', ' ':'_', ')':'', '/':'_' })


def RemoveListBlanks(src):
    return [el for el in src if el]


def List2DictKeys(List):
    Dictionary = defaultdict(list)
    for Item in List:
            Dictionary[Item] = ''
    return Dictionary


def AddToDict(FromDict, ToDict):
    for Key, Value in FromDict.items():
            if hasattr(Value, 'copy') and callable(getattr(Value, 'copy')):
                    ToDict[Key] = Value.copy()
            else:
                    ToDict[Key] = Value

def MergeDicts(Dict1, Dict2):
    """
    Returns a by-value copy contained the merged content of the 2 passed
    dictionaries
    """
    NewDict = defaultdict(list)
    AddToDict(Dict1, NewDict)
    AddToDict(Dict2, NewDict)
    return NewDict


def TruncLines(Str, NumLines, EOL="\n"):
    return EOL.join(Str.split(EOL)[0:NumLines])


def DeriveHTTPMethod(Method, Data):  # Derives the HTTP method from Data, etc
    DMethod = Method
    # Method not provided: Determine method from params
    if DMethod is None or DMethod == '':
        DMethod = 'GET'
        if Data != '' and Data is not None:
            DMethod = 'POST'
    return DMethod


def get_random_str(len):
    """function returns random strings of length len"""
    return base64.urlsafe_b64encode(os.urandom(len))[0:len]
