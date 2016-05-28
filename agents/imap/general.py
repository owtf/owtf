#!/usr/bin/env python
'''
Description: General purpose functions to assist OWTF Agents
'''

import imp
import os
import sys
from collections import defaultdict


class Plugin:
    '''
    Python fiddling to load a module from a file, there is probably a better way...
    '''
    def Get(self, ModuleName, ModuleFile, ModulePath):
        f, FileName, desc = imp.find_module(ModuleFile.split('.')[0], [ModulePath])
        return imp.load_module(ModuleName, f, FileName, desc)

    def Run(self, name, path, params):
        return self.Get("", name, "%s/" % path).Run(params)


class Storage:
    def __init__(self, FileName):
        self.FileName = FileName
        self.Init()
        self.Load()

    def Init(self):
        self.Content = ""

    def Get(self):
        return self.Content

    def Set(self, content):
        self.Content = content

    def Load(self):
        if not os.path.isfile(self.FileName):
            self.Init()
        else:
            self.Set(File().GetAsList(self.FileName)[0].strip())

    def Save(self):
        File().Save(self.FileName, self.Content)


class File:
    def GetAsList(self, FileName):
        try:
            output = open(FileName, 'r').read().split("\n")
            print "Loaded file: '%s'" % FileName
        except IOError:
            print "Cannot open file: '%s' (%s)" % (FileName, str(sys.exc_info()))
            output = []
        return output

    def Save(self, FileName, data):
        data = str(data)
        try:
            print "FileName=%s, Data=%s" % (FileName, str(data))
            print "Saving to File '%s' %s.." % (FileName, str(data))
            file = open(FileName, 'w')
            file.write(data)
        except IOError:
            print "Cannot write to: '%s' (%s)" % (FileName, str(sys.exc_info()))


class Config:
    def __init__(self, FileName):
        self.Config = defaultdict(list)
        self.Load(FileName)

    def Load(self, FileName):
        for line in File().GetAsList(FileName):
            try:
                name = line.split(":")[0]
                value = line.replace("%s:" % name, "").strip()
                self.Config[name] = value
            except ValueError:
                print "Cannot parse line: %s" % line

    def Get(self, setting):
        return self.Config[setting]

    def Set(self, setting, value):
        self.Config[setting] = value
