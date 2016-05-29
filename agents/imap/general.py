#!/usr/bin/env python
'''
Description: General purpose functions to assist OWTF Agents
'''

import imp
import os
from collections import defaultdict


class Plugin:
    def get(self, nodule_name, module_file, module_path):
        '''
        Python fiddling to load a module from a file, there is probably a better way...
        Like: ModulePath = os.path.abspath(ModuleFile)
        '''
        f, filename, desc = imp.find_module(module_file.split('.')[0], [module_path])
        return imp.load_module(module_name, f, filename, desc)

    def run(self, name, path, params):
        return self.get("", name, "%s/" % path).run(params)


class Storage:
    def __init__(self, file_name):
        self.filename = file_name
        self.init()
        self.load()
    
    def init(self):
        self.content = ""
        
    def get(self):
        return self.content
    
    def set(self, content):
        self.content = content
        
    def load(self):
        if not os.path.isfile(self.filename):
            self.init()
        else:
            self.set(File().get_as_list(self.filename)[0].strip())
    
    def save(self):
        File().save(self.filename, self.content)


class File:
    def get_as_list(self, file_name):
        try:
            output = open(file_name, 'r').read().split("\n")
            print "Loaded file: '%s'" % file_name
        except IOError, error:
            print "Cannot open file: '%s' (%s)" % (file_name, str(sys.exc_info()))
            output = []
        return output
    
    def save(self, file_name, data):
        data = str(data)
        try:
            print "Filename=%s, Data=%s" % (str(file_name), str(data))
            print "Saving to file '%s' %s.." % (str(file_name), str(data))
            f = open(file_name, 'w')
            f.write(data)
        except IOError, error:
            print "Cannot write to: '%s' (%s)" % (file_name, str(sys.exc_info()))


class Config:
    def __init__(self, file_name):
        self.config = defaultdict(list)
        self.load(file_name)
        
    def load(self, file_name):
        for line in File().get_as_list(file_name):
            try:
                name = line.split(":")[0]
                value = line.replace("%s:" % name, "").strip()
                self.config[name] = value
            except:
                print "Cannot parse line: %s" % line
                
    def get(self, setting):
        return self.config[setting]
    
    def set(self, setting, value):
        self.config[setting] = value
