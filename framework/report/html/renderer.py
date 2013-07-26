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
from jinja2 import Template, Environment

from framework.lib.general import *
from framework.report.html import tabcreator
from framework.report.html import tablecreator
import cgi

class HTMLRenderer:
	def __init__( self, Core ):
		self.Core = Core # Keep reference to config object, which needs to be used + passed on

	def CreateTabs( self ):
		return tabcreator.TabCreator( self )

	def CreateTable( self, Attribs = {} ):
		return tablecreator.TableCreator( self, Attribs )

	def DrawJSArrayFromList( self, List ): # Turns a Python List into a string to create a JavaScript Array
		template = Template( """
		new Array('{{ List|join("','") }}')
		""" )
		return template.render( List = List )

	def DrawiFrame( self, Attribs ):
		template = Template( """
		<iframe {% for Attrib, Value in Attribs.items() %}
		  			 {{ Attrib|e }}="{{ Value }}"
				{% endfor %}>
				Your browser does not support iframes
		</iframe>
		""" )
		return template.render( Attribs = Attribs )

	def DrawJSLink( self, Name, JSCode, Attribs = {}, IgnoredParam = '' ):
		Attribs['onclick'] = JSCode
		Attribs['target'] = ''
		template = Template( """
		<a href="javascript:void(0);" 
			{% for Attrib, Value in Attribs.items() %}
			   {{ Attrib|e }}="{{ Value }}"
			{% endfor %}
			>
			{{ Name }}
		</a>
		""" )
		return template.render( Name = Name, Attribs = Attribs )


	def DrawButtonJSLink( self, Name, JSCode, Attribs = None, IgnoredParam = '' ):
		Attribs['onclick'] = JSCode
		Attribs['target'] = ''
		if 'class' not in Attribs:
			Attribs['class'] = 'button' # By default set Links to button class
		template = Template( """
			<a href="javascript:void(0);" 
			{% for Attrib, Value in Attribs.items() %}
			   {{ Attrib|e }}="{{ Value }}"
			{% endfor %}
			>
			<span> {{ Name }} </span>
			</a>
		""" )
		return template.render( Name = Name, Attribs = Attribs )

	def GetAttribsAsStr( self, Attribs = {} ):
		template = Template( """
		{% for Attrib, Value in Attribs.items() %}
		   {{ Attrib|e }}="{{ Value }}"
		{% endfor %}
		""" )
		return template.render( Attribs = Attribs )

	def DrawImage( self, FileName, Attribs = {} ):
		template = Template( """
		<img src="images/{{ FileName }}.png" 
			{% for Attrib, Value in Attribs.items() %}
			   {{ Attrib|e }}="{{ Value }}"
			{% endfor %}
		>
		""" )
		return template.render( FileName = FileName, Attribs = Attribs )

	def RenderLink( self, Name, Link, Attribs = {} ):
		template = Template( """
			<a href="{{ Link }}" 
			{% for Attrib, Value in Attribs.items() %}
			   {{ Attrib|e }}="{{ Value }}"
			{% endfor %}
			>
			{{ Name }}
			</a>
		""" )
		return template.render( Link = Link, Name = Name, Attribs = Attribs )

	def GetPartialPathForLink( self, Link, ToFile = False, FromPlugin = False ):
		PartialPath = Link
		if str( ToFile ) == 'URL_OUTPUT': # Different transaction log for each URL = different link path for files
			PartialPath = PartialPath.replace( self.Core.Config.Get( 'URL_OUTPUT' ), '' )
		elif ToFile:
			PartialPath = self.Core.GetPartialPath( PartialPath )
		if FromPlugin:
			PartialPath = "../../../" + PartialPath # For HTML files built from a plugin
		return PartialPath

	def DrawLink( self, Name, Link, Attribs = {}, ToFile = False, FromPlugin = False ):
		#return '<a href="'+self.GetPartialPathForLink(Link, ToFile, FromPlugin)+'" target="_blank">'+Name+'</a>'
		if not 'target' in Attribs:
			Attribs['target'] = '_blank' # By default open everything in a new tab
		template = Template( """
			<a href="{{ Link }}" 
			{% for Attrib, Value in Attribs.items() %}
			   {{ Attrib|e }}="{{ Value }}"
			{% endfor %}
			>
			{{ Name }}
			</a>
		""" )
		return template.render( Link = self.GetPartialPathForLink( Link, ToFile, FromPlugin ), Name = Name, Attribs = Attribs )

	def DrawButtonLink( self, Name, Link, Attribs = {}, ToFile = False, FromPlugin = False ):
		if 'class' not in Attribs:
			Attribs['class'] = 'button' # By default set Links to button class
		if not 'target' in Attribs:
			Attribs['target'] = '_blank' # By default open everything in a new tab
		template = Template( """
			<a href="{{ Link }}" 
			{% for Attrib, Value in Attribs.items() %}
			   {{ Attrib|e }}="{{ Value }}"
			{% endfor %}
			>
			<span> {{ Name }} </span>
			</a>
		""" )
		return template.render( Link = self.GetPartialPathForLink( Link, ToFile, FromPlugin ), Name = Name, Attribs = Attribs )

	def DrawLinkPairs( self, PairList, Method = 'DrawLink', Attribs = {}, ToFile = False ):
		Links = []
		for LinkName, LinkURL in PairList:
			Links.append( CallMethod( self, Method, [LinkName, LinkURL, Attribs, ToFile] ) )
			#Links.append(self.DrawLink(LinkName, LinkURL, Attribs, ToFile))
		return Links

	def DrawHTMLList( self, ItemList, Attribs = { 'class' : 'default_list' } ):
		template = Template( """
		<ul  
		{% for Attrib, Value in Attribs.items() %}
		   {{ Attrib|e }}="{{ Value }}"
		{% endfor %}
		>
    		{% for Item in ItemList %}
    			<li>{{ Item }}</li>
    		{% endfor %}
		</ul>
		""" )
		return template.render( ItemList = ItemList, Attribs = Attribs )

	def DrawLinkPairsAsHTMLList( self, PairList, Method = 'DrawLink', Attribs = {}, ToFile = False ):
		#return "<ul><li>"+"</li><li>".join(self.DrawLinkPairs(PairList, Method, Attribs, ToFile))+"</li></ul>"
		Result = self.DrawHTMLList( self.DrawLinkPairs( PairList, Method, Attribs, ToFile ) )
		return Result

	def DrawButton( self, Name, JavaScript ):
		template = Template( """
		
		<button onclick="javascript: {{ JavaScript }}"> {{ Name }} </button>
		
		""" )
		return template.render( Name = Name, JavaScript = JavaScript, )
