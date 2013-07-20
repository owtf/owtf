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
import os, re, cgi
from framework.lib.general import *
from collections import defaultdict
import json

class Summary:
	def __init__(self, Core):
		self.Core = Core # Keep Reference to Core Object

	def InitNetMap(self):
		self.PluginsFinished = []
		self.NetMap = defaultdict(list)

	def InitMap(self, IP, Port):
		if IP not in self.NetMap:
			self.NetMap[IP] = defaultdict(list)
		if Port not in self.NetMap[IP]:
			self.NetMap[IP][Port] = []

	def GetSortedIPs(self):
		IPs = []
		for IP, Ports in self.NetMap.items():
			IPs.append(IP)
		return sorted(IPs)

	def GetSortedPorts(self, IP):
		Ports = []
		for Port, PortInfo in self.NetMap[IP].items():
			Ports.append(Port)
		return sorted(Ports)

	def AddToNetMap(self, Report):
		IP = Report['SummaryHostIP']
		Port = Report['SummaryPortNumber']
		self.InitMap(IP, Port)
		self.NetMap[IP][Port].append( Report['ReviewOffset'] )

	def MapReportsToNetMap(self, ReportType): 
		for Report in self.Core.DB.ReportRegister.Search( { 'ReportType' : ReportType } ):
			self.AddToNetMap(Report)

	def RenderNetMap(self):
		IPs = []
		for IP in self.GetSortedIPs():
			IPs.append(self.RenderIP(IP))
		return self.Core.Reporter.Render.DrawHTMLList(IPs, { 'class' : 'ip_list' } )

	def RenderIPValue(self, IP):
		return '<div id="' + cgi.escape(IP) + '">' + cgi.escape(IP) + '</div>'	

	def RenderIP(self, IP):
		Ports = []
		for Port in self.GetSortedPorts(IP):
			Ports.append(self.RenderPortInfo(IP, Port))
		return self.RenderIPValue(IP) + self.Core.Reporter.Render.DrawHTMLList(Ports, { 'class' : 'port_list' })

	def CountPluginsFinished(self, ReviewOffset):
		FinishedForOffset = len(self.Core.DB.PluginRegister.Search( { 'ReviewOffset' : ReviewOffset } ))
		self.PluginsFinished.append( { 'Offset' : ReviewOffset, 'NumFinished' : FinishedForOffset } )

	def IsOffsetUnReachable(self, ReviewOffset):
		OffsetPlugins = self.Core.DB.PluginRegister.Search( { 'ReviewOffset' : ReviewOffset } )
		if len(OffsetPlugins) > 0:
			Target = OffsetPlugins[0]['Target']
			#print "Target="+Target
			return self.Core.IsTargetUnreachable(Target)
		return False # Assume false until proven otherwise :P -must do this for passive testing + external plugins-

	def DrawHiddenOffsetIPAndPort(self, ReviewOffset, IP, Port): # Pass IP and Port mapping to offset for code simplification in JS
		return self.Core.Reporter.Render.DrawDiv(IP, { 'id' : 'ip_' + ReviewOffset, 'style' : 'display: none' })+self.Core.Reporter.Render.DrawDiv(Port, { 'id' : 'port_' + ReviewOffset, 'style' : 'display: none' })

	def RenderPortInfo(self, IP, Port):
		Offsets = []
		UnReachable = True
		for ReviewOffset in sorted(self.NetMap[IP][Port]):
			if self.IsOffsetUnReachable(ReviewOffset):
				continue # Skip targets that are not reachable in the summary
			#self.Core.IsTargetUnreachable()
			ReportPath = self.Core.DB.ReportRegister.Search( { 'ReviewOffset' : ReviewOffset } )[0]['ReportPath']
			#print "IP="+str(IP)+", Port="+str(Port)+" -> ReviewOffset="+str(ReviewOffset)+", ReportPath="+str(ReportPath)
			Offsets.append('<a name="anchor_'+ReviewOffset+'">'+self.Core.Reporter.Render.DrawiFrame( { 'id' : 'iframe_'+ReviewOffset, 'src' : self.Core.GetPartialPath(ReportPath), 'width' : '100%', 'height' : self.Core.Config.Get('COLLAPSED_REPORT_SIZE'), 'frameborder' : '0', 'class' : 'iframe_collapsed' })+"</a>" + self.DrawHiddenOffsetIPAndPort(ReviewOffset, IP, Port))
			self.CountPluginsFinished(ReviewOffset)
			UnReachable = False
			#Output += "IP="+IP+", Port="+Port+"->"+
		#print "UnReachable="+str(UnReachable)
		if UnReachable:
			Output = "&nbsp;" * 5 + "<strike>Port unreachable</strike>"
		else:
			Output = self.Core.Reporter.Render.DrawHTMLList(Offsets, { 'class' : 'review_offset_list' } )
		return self.RenderPortValue(Port) + Output

	def RenderPortValue(self, Port):
		return '<div id="' + cgi.escape(Port) + '">' + cgi.escape(Port) + '</div>'	

	def RenderAUX(self):
		AuxSearch = self.Core.DB.ReportRegister.Search( { 'ReportType' : 'AUX' } )
		if len(AuxSearch) > 0: # Aux plugin report present, link to it from summary
			# To be passed to JavaScript: AuxSearch[0]['ReviewOffset']
			return self.Core.Reporter.Render.DrawButtonLink('Auxiliary Plugins', self.Core.GetPartialPath(AuxSearch[0]['ReportPath']), { 'class' : 'report_index', 'target' : '' } )
		return "" # Nothing to show

	def ReportStart(self):
		self.Core.Reporter.CounterList = []
		self.Core.Reporter.Header.Save('HTML_REPORT_PATH', { 'ReportType' : 'NetMap', 'Title' : 'Summary Report' } )

	def ReportFinish(self):
		self.ReportStart()
		self.InitNetMap()
		self.MapReportsToNetMap('URL')
		HTML = self.RenderNetMap()
		HTML += self.RenderAUX()
		HTML += """
<script>
var DetailedReport = false
var AllCounters = new Array('filtermatches_counter','filterinfo_counter','filterno_flag_counter','filterunseen_counter','filterseen_counter','filternotes_counter','filterattention_orange_counter','filterbonus_red_counter','filterstar_3_counter','filterstar_2_counter','filtercheck_green_counter','filterbug_counter','filterflag_blue_counter','filterflag_yellow_counter','filterflag_red_counter','filterflag_violet_counter','filterdelete_counter','filteroptions_counter','filterrefresh_counter')
var CollapsedReportSize = '"""+self.Core.Config.Get('COLLAPSED_REPORT_SIZE')+"""'
var NetMap = """ + json.dumps(self.NetMap)+"""
var PluginDelim = '""" + self.Core.Reporter.GetPluginDelim() + """'
var SeverityWeightOrder = """ + self.Core.Reporter.Render.DrawJSArrayFromList(self.Core.Config.Get('SEVERITY_WEIGHT_ORDER').split(',')) + """
var PassedTestIcons = """ + self.Core.Reporter.Render.DrawJSArrayFromList(self.Core.Config.Get('PASSED_TEST_ICONS').split(',')) + """
</script>
</body>
</html>
"""
		with open(self.Core.Config.Get('HTML_REPORT_PATH'), 'a') as file:
			file.write(HTML) # Closing HTML Report
		cprint("Summary report written to: "+self.Core.Config.Get('HTML_REPORT_PATH'))

