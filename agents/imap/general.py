#!/usr/bin/env python
'''
Description:
General purpose functions to assist OWTF Agents
'''
import imp, os
from collections import defaultdict

class Plugin:
	def Get(self, ModuleName, ModuleFile, ModulePath):# Python fiddling to load a module from a file, there is probably a better way...
		f, Filename, desc = imp.find_module(ModuleFile.split('.')[0], [ModulePath]) #ModulePath = os.path.abspath(ModuleFile)
		return imp.load_module(ModuleName, f, Filename, desc)

	def Run(self, Name, Path, Params):
		return self.Get("", Name, Path+"/").Run(Params)

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
		#print "Saving Storage " + str(self.Content) + ".."
		File().Save(self.FileName, self.Content)

class File:
	def GetAsList(self, FileName):
		try:
			Output = open(FileName, 'r').read().split("\n")
			print "Loaded file: '"+FileName+"'"
		except IOError, error:
			print "Cannot open file: '"+FileName+"' ("+str(sys.exc_info())+")"
			Output = []
		return Output
	
	def Save(self, FileName, Data):
		Data = str(Data)
		try:
			print "FileName=" + str(FileName) + ", Data=" + str(Data)
			print "Saving to File '" + str(FileName) + "' " + str(Data) + ".."
			File = open(FileName, 'w')
			File.write(Data)
		except IOError, error:
			print "Cannot write to: '" + FileName +"' ("+str(sys.exc_info())+")"

class Config:
	def __init__(self, FileName):
		self.Config = defaultdict(list)
		self.Load(FileName)
		
	def Load(self, FileName):
		for Line in File().GetAsList(FileName):
			try:
				Name = Line.split(":")[0]
				Value = Line.replace(Name + ":", "").strip()
				self.Config[Name] = Value
			except:
				print "Cannot parse line: " + Line
				
	def Get(self, Setting):
		return self.Config[Setting]
	
	def Set(self, Setting, Value):
		self.Config[Setting] = Value
