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
from jinja2 import Environment, PackageLoader
from framework.lib.general import *
from collections import defaultdict
import logging
import os
import re
import cgi

PLUGIN_DELIM = '__'  # Characters like ; | . or / trip CKEditor as separators

class Summary:
	def __init__( self, Core ):
		self.Core = Core # Keep Reference to Core Object
		self.Template_env = env = Environment( loader = PackageLoader( 'framework.report', 'templates' ) )


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
			self.Core.Config.SetTarget(ReviewOffset)
			Offsets.append( {
								"ReviewOffset": ReviewOffset,
								"ReviewPath": self.Core.GetPartialPath( ReportPath ),
								"Logs":	 {
											"Transaction_Log_HTML": {
																		"link": self.Core.Config.Get( 'TRANSACTION_LOG_HTML' ),
																	},
									    	"All_Downloaded_Files": {
																		"link": '#',
																	},
										    "All_Transactions": {
																	"link": self.Core.Config.Get( 'TRANSACTION_LOG_TRANSACTIONS' ),
																},
											"All_Requests": {
																"link": self.Core.Config.Get( 'TRANSACTION_LOG_REQUESTS' ),
															},
											"All_Response_Headers": {
																		"link": self.Core.Config.Get( 'TRANSACTION_LOG_RESPONSE_HEADERS' ),
																	},
											"All_Response_Bodies": {
																		"link": self.Core.Config.Get( 'TRANSACTION_LOG_RESPONSE_BODIES' ),
																	},
										},
								"Urls":  {
										    "All_URLs_link": self.Core.Config.Get( 'ALL_URLS_DB' ),
									    	"File_URLs_link": self.Core.Config.Get( 'FILE_URLS_DB' ),
										    "Fuzzable_URLs_link": self.Core.Config.Get( 'FUZZABLE_URLS_DB' ),
											"Image_URLs_link":  self.Core.Config.Get( 'IMAGE_URLS_DB' ),
											"Error_URLs_link": self.Core.Config.Get( 'ERROR_URLS_DB' ),
											"External_URLs_link":  self.Core.Config.Get( 'EXTERNAL_URLS_DB' ),
											"SSI_URLs_link":  self.Core.Config.Get( 'SSI_URLS_DB' ),
										},
								"Urls_Potential":  {
										    "All_URLs_link": self.Core.Config.Get( 'POTENTIAL_ALL_URLS_DB' ),
									    	"File_URLs_link": self.Core.Config.Get( 'POTENTIAL_FILE_URLS_DB' ),
										    "Fuzzable_URLs_link": self.Core.Config.Get( 'POTENTIAL_FUZZABLE_URLS_DB' ),
											"Image_URLs_link":  self.Core.Config.Get( 'POTENTIAL_IMAGE_URLS_DB' ),
											"Error_URLs_link": self.Core.Config.Get( 'POTENTIAL_ERROR_URLS_DB' ),
											"External_URLs_link":  self.Core.Config.Get( 'POTENTIAL_EXTERNAL_URLS_DB' ),
											"SSI_URLs_link":  self.Core.Config.Get( 'POTENTIAL_SSI_URLS_DB' ),
										}
							})
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


	def ReportFinish( self ):
		self.Core.Reporter.CounterList = []
		#self.TargetOutputDir, self.FrameworkDir, self.Version, self.Release, self.TargetURL, self.HostIP, self.PortNumber, self.TransactionLogHTML, self.AlternativeIPs = self.Core.Config.GetAsList( ['OUTPUT_PATH', 'FRAMEWORK_DIR', 'VERSION', 'RELEASE', 'TARGET_URL', 'HOST_IP', 'PORT_NUMBER', 'TRANSACTION_LOG_HTML', 'ALTERNATIVE_IPS'] )
		if not self.Core.Reporter.Init:
			self.Core.Reporter.CopyAccessoryFiles()
			self.Core.Reporter.Init = True # The report is re-generated several times, this ensures images, stylesheets, etc are only copied once at the start

		self.InitNetMap()
		self.MapReportsToNetMap( 'URL' )
		template = self.Template_env.get_template( 'summary.html' )

		vars = {
						"Seed": self.Core.GetSeed(),
						"Version": self.Core.Config.Get( 'VERSION' ),
						"Release": self.Core.Config.Get( 'RELEASE' ),
						"HTML_REPORT": self.Core.Config.Get( 'HTML_REPORT' ),
						"TargetLink": self.Core.Config.Get( 'TARGET_URL' ),
						"HostIP":  self.Core.Config.Get( 'HOST_IP' ),
						"AlternativeIPs": self.Core.Config.Get( 'ALTERNATIVE_IPS' ),
						"PortNumber":  self.Core.Config.Get( 'PORT_NUMBER' ),
						"RUN_DB": self.Core.DB.GetData( 'RUN_DB' ),
						"PluginTypes": self.Core.Config.Plugin.GetAllGroups(),
						"WebPluginTypes": self.Core.Config.Plugin.GetTypesForGroup( 'web' ),
						"AuxPluginTypes": self.Core.Config.Plugin.GetTypesForGroup( 'aux' ),
						"NetPluginTypes": self.Core.Config.Plugin.GetTypesForGroup( 'net' ),
						"WebTestGroups":self.Core.Config.Plugin.GetWebTestGroups(),
						"Logs": {
								 "Errors": {
											  "nb": self.Core.DB.GetLength( 'ERROR_DB' ),
											  "link":  str( self.Core.Config.Get( 'ERROR_DB' ) )
											},
							    "Unreachables": {
											  "nb": self.Core.DB.GetLength( 'UNREACHABLE_DB' ),
											  "link":  str( self.Core.Config.Get( 'UNREACHABLE_DB' ) ) ,
												 }
							      },
						"IPs": [{
								"IP": IP,
								"Ports": [ self.PortInfo( IP, Port ) for Port in self.GetSortedPorts( IP )]
								} for IP in self.GetSortedIPs()],
						"Stats": {
								"Targets": sum([len(self.GetSortedPorts(IP)) for IP in self.GetSortedIPs() ]),
								},
						"AuxInfo":  self.AuxInfo(),
						"JsonNetMap": json.dumps( self.NetMap ),
                        "PLUGIN_DELIM" : PLUGIN_DELIM,

				}

		HTML = template.render(vars)
		with self.Core.codecs_open(self.Core.Config.Get('HTML_REPORT_PATH' ), 'w',"utf-8") as file:
			file.write(HTML) # Closing HTML Report
		log("Summary report written to: "+self.Core.Config.Get('HTML_REPORT_PATH'))


