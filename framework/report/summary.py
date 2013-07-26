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

The reporter module is in charge of producing the HTML Report as well as provide plugins with common HTML Rendering functions
'''
import json
from jinja2 import Template
from framework.lib.general import *
from collections import defaultdict


class Summary:
	def __init__( self, Core ):
		self.Core = Core # Keep Reference to Core Object

	def InitNetMap( self ):
		self.PluginsFinished = []
		self.NetMap = defaultdict( list )

	def InitMap( self, IP, Port ):
		if IP not in self.NetMap:
			self.NetMap[IP] = defaultdict( list )
		if Port not in self.NetMap[IP]:
			self.NetMap[IP][Port] = []

	def GetSortedIPs( self ):
		IPs = []
		for IP, Ports in self.NetMap.items():
			IPs.append( IP )
		return sorted( IPs )

	def GetSortedPorts( self, IP ):
		Ports = []
		for Port, PortInfo in self.NetMap[IP].items():
			Ports.append( Port )
		return sorted( Ports )

	def AddToNetMap( self, Report ):
		IP = Report['SummaryHostIP']
		Port = Report['SummaryPortNumber']
		self.InitMap( IP, Port )
		self.NetMap[IP][Port].append( Report['ReviewOffset'] )

	def MapReportsToNetMap( self, ReportType ):
		for Report in self.Core.DB.ReportRegister.Search( { 'ReportType' : ReportType } ):
			self.AddToNetMap( Report )


	def CountPluginsFinished( self, ReviewOffset ):
		FinishedForOffset = len( self.Core.DB.PluginRegister.Search( { 'ReviewOffset' : ReviewOffset } ) )
		self.PluginsFinished.append( { 'Offset' : ReviewOffset, 'NumFinished' : FinishedForOffset } )

	def IsOffsetUnReachable( self, ReviewOffset ):
		OffsetPlugins = self.Core.DB.PluginRegister.Search( { 'ReviewOffset' : ReviewOffset } )
		if len( OffsetPlugins ) > 0:
			Target = OffsetPlugins[0]['Target']
			#print "Target="+Target
			return self.Core.IsTargetUnreachable( Target )
		return False # Assume false until proven otherwise :P -must do this for passive testing + external plugins-


	def PortInfo( self, IP, Port ):
		Offsets = []
		UnReachable = True
		for ReviewOffset in sorted( self.NetMap[IP][Port] ):
			if self.IsOffsetUnReachable( ReviewOffset ):
				continue # Skip targets that are not reachable in the summary
			#self.Core.IsTargetUnreachable()
			ReportPath = self.Core.DB.ReportRegister.Search( { 'ReviewOffset' : ReviewOffset } )[0]['ReportPath']
			#print "IP="+str(IP)+", Port="+str(Port)+" -> ReviewOffset="+str(ReviewOffset)+", ReportPath="+str(ReportPath)
			Offsets.append( {"ReviewOffset": ReviewOffset, "ReviewPath": self.Core.GetPartialPath( ReportPath )} )
			self.CountPluginsFinished( ReviewOffset )
			UnReachable = False

		return {  "Port": Port,
				  "UnReachable": UnReachable,
				  "Offsets": Offsets
				 }

	def AuxInfo( self ):
		AuxSearch = self.Core.DB.ReportRegister.Search( { 'ReportType' : 'AUX' } )
		if len( AuxSearch ) > 0:
			AuxLink = self.Core.GetPartialPath( AuxSearch[0]['ReportPath'] )
		else:
			AuxLink = None

		return {
					"AuxSearch":AuxSearch,
					"AuxLink": AuxLink
				}

	def ReportStart( self ):
		self.Core.Reporter.CounterList = []
		self.Core.Reporter.Header.Save( 'HTML_REPORT_PATH', { 'ReportType' : 'NetMap', 'Title' : 'Summary Report' } )

	def ReportFinish( self ):
		self.ReportStart()
		self.InitNetMap()
		self.MapReportsToNetMap( 'URL' )
		template = Template( """
			<!-- NetMap -->
			<ul class="ip_list">
				{% for IPInfo in IPs %}
					<li>
					<div id="{{ IPInfo.IP|e }}"> {{ IPInfo.IP|e }} </div>
					<ul  class="port_list">
			    		{% for PortInfo in IPInfo.Ports %}
			    			<li>
								<div id="{{ PortInfo.Port|e }}"> {{ PortInfo.Port|e }} </div>
								{% if PortInfo.UnReachable %}
									<strike>Port unreachable</strike>
								{% else %}
									&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
											<ul class='review_offset_list'>
									    		{% for Offset in PortInfo.Offsets %}
									    			<li>
									    				<a name="anchor_{{ Offset.ReviewOffset }}">
									    					<iframe id="iframe_{{ Offset.ReviewOffset }}" src="{{ Offset.ReviewPath }}" width= '100%' height = "{{ COLLAPSED_REPORT_SIZE }}"  frameborder = '0' class = 'iframe_collapsed' >
																Your browser does not support iframes
															</iframe>
														</a>
														<div id="ip_{{ Offset.ReviewOffset }}" style = 'display: none'>{{ IPInfo.IP }}</div>
														<div id="port_{{ Offset.ReviewOffset }}" style = 'display: none'>{{ PortInfo.Port }}</div>
									    			</li>
									    		{% endfor %}
											</ul>
								{% endif %}
							</li>
			    		{% endfor %}
					</ul>
					</li>
				{% endfor %}
			</ul>
			<!-- end NetMap -->
			<!-- start AUX -->
			{% if AuxInfo.AuxSearch|count %}
				<a href="{{ AuxInfo.AuxLink }}" class='report_index'>
					<span> Auxiliary Plugins </span>
				</a>
			{% endif %}
			<!-- end AUX -->
		<script>
		var DetailedReport = false
		var AllCounters = new Array('filtermatches_counter','filterinfo_counter','filterno_flag_counter','filterunseen_counter','filterseen_counter','filternotes_counter','filterattention_orange_counter','filterbonus_red_counter','filterstar_3_counter','filterstar_2_counter','filtercheck_green_counter','filterbug_counter','filterflag_blue_counter','filterflag_yellow_counter','filterflag_red_counter','filterflag_violet_counter','filterdelete_counter','filteroptions_counter','filterrefresh_counter')
		var CollapsedReportSize = '{{ COLLAPSED_REPORT_SIZE }}'
		var NetMap = {{ JsonNetMap }}
		var PluginDelim = '{{ PLUGIN_DELIM }}'
		var SeverityWeightOrder = new Array('bonus_red','flag_violet','flag_red','flag_yellow','flag_blue','bug')
		var PassedTestIcons = new Array('check_green')
</script>
</body>
</html>
		
		""" )




		vars = {
					"IPs": [{
							"IP": IP,
							"Ports": [ self.PortInfo( IP, Port ) for Port in self.GetSortedPorts( IP )]
							} for IP in self.GetSortedIPs()],
					"AuxInfo":  self.AuxInfo(),
					"COLLAPSED_REPORT_SIZE": self.Core.Config.Get( 'COLLAPSED_REPORT_SIZE' ),
					"JsonNetMap": json.dumps( self.NetMap ),
					"PLUGIN_DELIM":  self.Core.Reporter.GetPluginDelim(),
				}

		HTML = template.render( vars )
		with open( self.Core.Config.Get( 'HTML_REPORT_PATH' ), 'a' ) as file:
			file.write( HTML ) # Closing HTML Report
		cprint( "Summary report written to: " + self.Core.Config.Get( 'HTML_REPORT_PATH' ) )

