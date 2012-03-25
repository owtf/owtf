#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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