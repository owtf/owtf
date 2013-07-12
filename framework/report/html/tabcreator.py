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

The tab module simplifies tab creation via CSS
'''
from jinja2 import Template
from framework.lib.general import *

class TabCreator:
	def __init__( self, Renderer ):
		self.Renderer = Renderer
		self.Config = self.Renderer.Core.Config # Shortcut to config
		self.Tabs = [] # List to contain drawn tab text
		self.DivContent = [] # List to contain the drawn div content
		self.DivIdList = []
		self.TabIdList = []
		self.TabList = [] # Holds relationship of divid, tabid and tabname, important for rendering and js
		self.FlowButtons = []

	def GetNumDivs( self ):
		return len( self.DivIdList )

	def AddCustomDiv( self, TabContent, DivContent = '' ):
		Custom = True
		self.TabList.append( [ '', '', TabContent, DivContent, Custom ] )

	def AddDiv( self, DivId, TabName, DivContent ):
		Custom = False
		self.DivIdList.append( DivId )
		TabId = self.GetTabIdForDiv( DivId )
		self.TabList.append( [ DivId, TabId, TabName, DivContent, Custom ] )
		self.TabIdList.append( TabId ) # Derive Tab Ids from Div Ids
		#print "Added div="+DivId+", TabName="+TabName
		#print "TabList="+str(self.TabList)
		#print "TabIdList="+str(self.TabIdList)

	def AddDivs( self, DivIdTabNamePairList ):
		for DivId, TabName in DivIdTabNamePairList:
			self.AddDiv( DivId, TabName )

	def GetTabIdForDiv( self, DivId ):
		return 'tab_' + DivId

	def ShowDivs( self ):
		template = Template( """
		ShowDivs(new Array('{{ List|join("','") }}'));
		""" )
		return template.render( List = self.DivIdList )

	def HideDivs( self ):
		template = Template( """
		HideDivs(new Array('{{ List|join("','") }}'));
		""" )
		return template.render( List = self.DivIdList )

	def UnhighlightTabs( self ):
		template = Template( """
		SetClassNameToElems(new Array('{{ TabIdList|join("','") }}'), '');
		""" )
		return template.render( TabIdList = self.TabIdList )

	def DrawTab( self, TabInfo ):
		DivId, TabId, TabName, DivContent, Custom = TabInfo
		template = Template( """
		<li>
			 {% if  Custom %}
				{{ TabName }}
			 {% else %}
				<a href="javascript:void(0);" id="{{ TabId }}" target=""
						onclick="SetClassNameToElems(new Array('{{ TabIdList|join("','") }}'), '');
								 HideDivs(new Array('{{ DivIdList|join("','") }}'));
								 this.className = 'selected'; 
								 ToggleDiv('{{ DivId }}');" >
					{{ TabName }}
				</a>
			 {% endif %}
		</li>
		""" )
		return [template.render( Custom = Custom, TabIdList = self.TabIdList, DivIdList = self.DivIdList, DivId = DivId, TabId = TabId, TabName = TabName ), DivContent]

	def CreateRawTab( self, RawTab, RawDivContent ):
		self.Tabs.append( RawTab )
		self.DivContent.append( RawDivContent )

	def CreateCustomTab( self, TabContent, DivContent = '' ):
		self.CreateRawTab( "<li>" + TabContent + "</li>", DivContent )

	def CreateTab( self, TabInfo ):
		TabContent, DivContent = self.DrawTab( TabInfo )
		DivId, TabId, TabName, DivContent, Custom = TabInfo
		self.CreateRawTab( TabContent, '<div id="' + DivId + '" class="tabContent" style="display:none">' + DivContent + '</div>' )

	def CreateTabs( self ):
		#p(self.TabList)
		for TabInfo in self.TabList:
			#print "TabInfo in loop="+str(TabInfo)
			self.CreateTab( TabInfo )

	def CreateTabButtons( self ):
		# -> working before but ugly: see tabs behind icons -> self.CreateCustomTab(self.DrawTabFlowButtons())
		self.CreateRawTab( '<li class="icon">' + self.DrawTabFlowButtons() + '</li>', '' )
		#self.FlowButtons = self.DrawTabFlowButtons()

	def DrawImageFromConfigPair( self, ConfigList ):
		#FileName, ToolTip = self.Core.Config.GetAsList(ConfigList)
		FileName, ToolTip = self.Config.GetAsList( ConfigList )
		template = Template( """		
					<img src="images/{{ FileName }}.png" title="{{ ToolTip }}">
				""" )
		return template.render( FileName = FileName, ToolTip = ToolTip )

	def DrawTabFlowButtons( self ):
		self.DrawImageFromConfigPair( [ 'FIXED_ICON_NOTES', 'REVIEW_TOOLTIP_NOTES' ] )
		template = Template( """		
					<img src="images/{{ FileName }}.png" title="{{ ToolTip }}">&nbsp;
					
				""" )
		#return template.render( FileName = FileName, ToolTip = ToolTip )
		return "&nbsp;".join( self.Renderer.DrawLinkPairs( [
[self.DrawImageFromConfigPair( [ 'FIXED_ICON_EXPAND_PLUGINS', 'NAV_TOOLTIP_EXPAND_PLUGINS' ] ), self.ShowDivs() + self.UnhighlightTabs() ]
, [self.DrawImageFromConfigPair( [ 'FIXED_ICON_CLOSE_PLUGINS', 'NAV_TOOLTIP_CLOSE_PLUGINS' ] ), self.HideDivs() + self.UnhighlightTabs()]
], 'DrawButtonJSLink', { 'class' : 'icon' } ) ) + self.Renderer.DrawButtonJSLink( '&nbsp;' + self.DrawImageFromConfigPair( [ 'FIXED_ICON_PLUGIN_INFO', 'FILTER_TOOLTIP_INFO_UNFILTER' ] ), self.UnhighlightTabs() + 'UnfilterBrotherTabs(this)', { 'class' : 'icon_unfilter', 'style' : 'display: none;' } )
		#return "&nbsp;".join(self.Renderer.DrawLinkPairs( [ ["<img src='images/arrow_down16x16.png' />", self.ShowDivs()+self.UnhighlightTabs() ], ["<img src='images/arrow_up16x16.png' />", self.HideDivs()+self.UnhighlightTabs()] ], 'DrawButtonJSLink', { 'class' : 'icon' }))

	def RenderTabs( self, Attribs = {} ):
		template = Template( """
		<ul id="tabs"
			{% for Attrib, Value in Attribs.items() %}
			{{ Attrib|e }}="{{ Value }}"
			{% endfor %}
			>
			{{ Tabs|join("\n") }}
		</ul>
			{{ FlowButtons|join }}
		""" )
		return template.render( Attribs = Attribs, Tabs = self.Tabs, FlowButtons = self.FlowButtons )

	def RenderDivs( self ):
		template = Template( """  {{ DivContent|join }} """ )
		return unicode( template.render( DivContent = self.DivContent ) )

	def Render( self, Attribs = {} ):
		return self.RenderTabs( Attribs ) + self.RenderDivs()
