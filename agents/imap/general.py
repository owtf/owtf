#!/usr/bin/env python
'''
Description:
General purpose functions to assist OWTF Agents
'''

import imp
import os
import sys
from collections import defaultdict


class Plugin:
    # Python fiddling to load a module from a file, there is probably a better way...
    def Get(self, ModuleName, ModuleFile, ModulePath):
        f, Filename, desc = imp.find_module(ModuleFile.split('.')[0], [ModulePath])
        return imp.load_module(ModuleName, f, Filename, desc)

    def Run(self, Name, Path, Params):
        return self.Get("", Name, "%s/" % Path).Run(Params)


class Storage:
    def __init__(self, FileName):
        self.FileName = FileName
        self.Init()
        self.Load()

    def Init(self):
        self.Content = ""

    def Get(self):
        return self.Content

    def Set(self, Content):
        self.Content = Content

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
            Output = open(FileName, 'r').read().split("\n")
            print "Loaded file: '%s'" % FileName
        except IOError:
            print "Cannot open file: '%s' (%s)" % (FileName, str(sys.exc_info()))
            Output = []
        return Output

    def Save(self, FileName, Data):
        Data = str(Data)
        try:
            print "FileName=%s, Data=%s" % (FileName, str(Data))
            print "Saving to File '%s' %s.." % (FileName, str(Data))
            File = open(FileName, 'w')
            File.write(Data)
        except IOError:
            print "Cannot write to: '%s' (%s)" % (FileName, str(sys.exc_info()))


class Config:
    def __init__(self, FileName):
        self.Config = defaultdict(list)
        self.Load(FileName)

    def Load(self, FileName):
        for Line in File().GetAsList(FileName):
            try:
                Name = Line.split(":")[0]
                Value = Line.replace("%s:" % Name, "").strip()
                self.Config[Name] = Value
            except:
                print "Cannot parse line: %s" % Line

    def Get(self, Setting):
        return self.Config[Setting]

    def Set(self, Setting, Value):
        self.Config[Setting] = Value
