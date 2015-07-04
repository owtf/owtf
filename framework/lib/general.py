#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
