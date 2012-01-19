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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
                                                                                                           

This library contains helper functions and exceptions for the framework
"""
from framework.lib.general import *
from framework.report.html import tabcreator
from framework.report.html import tablecreator
import cgi

class HTMLRenderer:
	def __init__(self, Core):
		self.Core = Core # Keep reference to config object, which needs to be used + passed on

	def CreateTabs(self):
		return tabcreator.TabCreator(self)

	def CreateTable(self, Attribs = {}):
		return tablecreator.TableCreator(self, Attribs)

	def DrawJSArrayFromList(self, List): # Turns a Python List into a string to create a JavaScript Array
		return "new Array('"+"','".join(List)+"')"

	def GetAttribsForJS(self, JSCode, Attribs):
		Attribs['onclick'] = JSCode
		Attribs['target'] = ''
		return Attribs

	def DrawiFrame(self, Attribs):
		return "<iframe "+self.GetAttribsAsStr(Attribs)+">Your browser does not support iframes</iframe>"

	def DrawJSLink(self, Name, JSCode, Attribs = {}, IgnoredParam = ''):
		Attribs = self.GetAttribsForJS(JSCode, Attribs)
		return self.DrawLink(Name, 'javascript:void(0);', Attribs)

	def DrawButtonJSLink(self, Name, JSCode, Attribs = None, IgnoredParam = ''):
		Attribs = self.GetAttribsForJS(JSCode, Attribs) 
		return self.DrawButtonLink(Name, 'javascript:void(0);', Attribs)

	def GetAttribsAsStr(self, Attribs = {}):
		AttribStr = ""
		for Attrib, Value in Attribs.items():
			AttribStr += " "+Attrib+'="'+Value+'"'
		return AttribStr

	def DrawImage(self, FileName, Attribs = {}):
                if len(FileName.split('.')) == 1:# No extension = append ".png"
                        FileName += '.png'
                return '<img src="images/'+FileName+'" '+self.GetAttribsAsStr(Attribs)+'>'

	def RenderLink(self, Name, Link, Attribs = {}):
		#print "Link="+str(Link)+", Attribs="+str(self.GetAttribsAsStr(Attribs))+", Name="+Name	
		return '<a href="'+Link+'" '+self.GetAttribsAsStr(Attribs)+'>'+Name+'</a>'

	def GetPartialPathForLink(self, Link, ToFile = False, FromPlugin = False):
		PartialPath = Link
		if str(ToFile) == 'URL_OUTPUT': # Different transaction log for each URL = different link path for files
			PartialPath = PartialPath.replace(self.Core.Config.Get('URL_OUTPUT'), '')
		elif ToFile:
			PartialPath = self.Core.GetPartialPath(PartialPath)
		if FromPlugin:
			PartialPath = "../../../"+PartialPath # For HTML files built from a plugin
		return PartialPath

	def DrawLink(self, Name, Link, Attribs = {}, ToFile = False, FromPlugin = False):
		#return '<a href="'+self.GetPartialPathForLink(Link, ToFile, FromPlugin)+'" target="_blank">'+Name+'</a>'
		if not 'target' in Attribs:
			Attribs['target'] = '_blank' # By default open everything in a new tab
		return self.RenderLink(Name, self.GetPartialPathForLink(Link, ToFile, FromPlugin), Attribs)

	def DrawButtonLink(self, Name, Link, Attribs = {}, ToFile = False, FromPlugin = False):
		#print "Name="+Name+", Link="+Link
		if 'class' not in Attribs:
			Attribs['class'] = 'button' # By default set Links to button class
		return self.DrawLink('<span>'+Name+'</span>', Link, Attribs, ToFile, FromPlugin)
		#return '<a class="button" href="'+self.GetPartialPathForLink(Link, ToFile, FromPlugin)+'" target="_blank"><span>'+Name+'</span></a>'
		#return self.RenderLink('<span>'+Name+'</span>', self.GetPartialPathForLink(Link, ToFile, FromPlugin), { 'target' : '_blank' })

	def DrawLinkPairs(self, PairList, Method = 'DrawLink', Attribs = {}, ToFile = False):
		Links = []
		for LinkName, LinkURL in PairList:
			Links.append(CallMethod(self, Method, [LinkName, LinkURL, Attribs, ToFile]))
			#Links.append(self.DrawLink(LinkName, LinkURL, Attribs, ToFile))
		return Links

	def DrawHTMLList(self, ItemList, Attribs = { 'class' : 'default_list' }):
		return "<ul"+self.GetAttribsAsStr(Attribs)+"><li>"+"</li><li>".join(ItemList)+"</li></ul>"

	def DrawLinkPairsAsHTMLList(self, PairList, Method = 'DrawLink', Attribs = {}, ToFile = False):
		#return "<ul><li>"+"</li><li>".join(self.DrawLinkPairs(PairList, Method, Attribs, ToFile))+"</li></ul>"
		Result = self.DrawHTMLList(self.DrawLinkPairs(PairList, Method, Attribs, ToFile))
		return Result

	def DrawButton(self, Name, JavaScript):
		return '<button onclick="javascript:'+JavaScript+'">'+Name+'</button>'

