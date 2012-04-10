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

The DB stores HTTP transactions, unique URLs and more. 
'''
import re
from framework.lib.general import *

class URLManager:
	NumURLsBefore = 0

	def __init__(self, Core):
		self.Core = Core
		# Compile regular expressions once at the beginning for speed purposes:
		self.IsFileRegexp = re.compile(Core.Config.Get('REGEXP_FILE_URL'), re.IGNORECASE)
		self.IsSmallFileRegexp = re.compile(Core.Config.Get('REGEXP_SMALL_FILE_URL'), re.IGNORECASE)
		self.IsImageRegexp = re.compile(Core.Config.Get('REGEXP_IMAGE_URL'), re.IGNORECASE)
		self.IsURLRegexp = re.compile(Core.Config.Get('REGEXP_VALID_URL'), re.IGNORECASE)

	def IsRegexpURL(self, URL, Regexp):
		if len(Regexp.findall(URL)) > 0:
			return True
		return False

	def IsSmallFileURL(self, URL):
		return self.IsRegexpURL(URL, self.IsSmallFileRegexp)

	def IsFileURL(self, URL):
		return self.IsRegexpURL(URL, self.IsFileRegexp)

	def IsImageURL(self, URL):
		return self.IsRegexpURL(URL, self.IsImageRegexp)

	def GetURLsToVisit(self, URLList):
		NewList = []
		for URL in URLList:
			if not self.IsImageURL(URL):
				NewList.append(URL)
		return NewList

	def IsURL(self, URL):
		return self.IsRegexpURL(URL, self.IsURLRegexp)

	def GetNumURLs(self, DBPrefix = "POTENTIAL_"):
		return self.Core.DB.GetLength(DBPrefix+'ALL_URLS_DB')
		#return len(self.Core.DB.DBCache[DBPrefix+'ALL_URLS_DB'])

	def IsURLAlreadyAdded(self, URL, DBPrefix = ''):
		return URL in self.Core.DB.GetData(DBPrefix+'ALL_URLS_DB') or URL in self.Core.DB.GetData(DBPrefix+'EXTERNAL_URLS_DB') or URL in self.Core.DB.GetData(DBPrefix+'ERROR_URLS_DB')
		#return URL in self.Core.DB.DBCache[DBPrefix+'ALL_URLS_DB'] or URL in self.Core.DB.DBCache[DBPrefix+'EXTERNAL_URLS_DB'] or URL in self.Core.DB.DBCache[DBPrefix+'ERROR_URLS_DB']

	def AddURLToDB(self, URL, DBPrefix = '', Found = None):
		Message = ''
		DBName = "vetted DB"
		if DBPrefix != "":
			DBName = "potential DB"
		if not self.IsURLAlreadyAdded(URL, DBPrefix) and self.IsURL(URL): # New URL
			URL = URL.strip() # Make sure URL is clean prior to saving in DB, nasty bugs can happen without this
			if self.Core.IsInScopeURL(URL):
				Message = cprint("Adding new URL to "+DBName+": "+URL)
				if Found in [ None, True ]:
					#self.Core.DB.DBCache[DBPrefix+'ALL_URLS_DB'].append(URL)
					self.Core.DB.Add(DBPrefix+'ALL_URLS_DB', URL)
					if self.IsFileURL(URL): # Classify URL for testing later:
						#self.Core.DB.DBCache[DBPrefix+'FILE_URLS_DB'].append(URL)
						self.Core.DB.Add(DBPrefix+'FILE_URLS_DB', URL)
					elif self.IsImageURL(URL):
						#self.Core.DB.DBCache[DBPrefix+'IMAGE_URLS_DB'].append(URL)
						self.Core.DB.Add(DBPrefix+'IMAGE_URLS_DB', URL)
					else:
						#self.Core.DB.DBCache[DBPrefix+'FUZZABLE_URLS_DB'].append(URL)
						self.Core.DB.Add(DBPrefix+'FUZZABLE_URLS_DB', URL)
				else: # Some error code (404, etc)
					#self.Core.DB.DBCache[DBPrefix+'ERROR_URLS_DB'].append(URL)
					self.Core.DB.Add(DBPrefix+'ERROR_URLS_DB', URL)
			else:
				Message = cprint("Adding new EXTERNAL URL to EXTERNAL "+DBName+": "+URL)
				#self.Core.DB.DBCache[DBPrefix+'EXTERNAL_URLS_DB'].append(URL)
				self.Core.DB.Add(DBPrefix+'EXTERNAL_URLS_DB', URL)
		return Message

	def AddURL(self, URL, Found = None): # Adds a URL to the relevant DBs if not already added
		DBPrefix = "POTENTIAL_"
		if Found != None: # Visited URL -> Found in [ True, False ]
			DBPrefix = ""
		return self.AddURLToDB(URL, DBPrefix, Found)

	def AddURLsStart(self):
		self.NumURLsBefore = self.GetNumURLs()

	def AddURLsEnd(self):
		NumURLsAfter = self.GetNumURLs()
		return cprint(str(NumURLsAfter-self.NumURLsBefore)+" URLs have been added and classified")

	def ImportURLs(self, URLList): # Extracts and classifies all URLs passed. Expects a newline separated URL list
		self.AddURLsStart()
		for URL in URLList:
			self.AddURL(URL)
		Message = self.AddURLsEnd()
		cprint(Message)
		return Message