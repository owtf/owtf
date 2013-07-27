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
import os, re, cgi, sys
from jinja2 import Environment, PackageLoader
from framework.lib.general import *
from collections import defaultdict

class Header:
	def __init__( self, CoreObj ):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False
		self.Template_env = env = Environment( loader = PackageLoader( 'framework.report', 'templates' ) )

        def CopyAccessoryFiles( self ):
                cprint( "Copying report images .." )
                self.Core.Shell.shell_exec( "cp -r " + self.FrameworkDir + "/images/ " + self.TargetOutputDir )
                cprint( "Copying report includes (stylesheet + javascript files).." )
                self.Core.Shell.shell_exec( "cp -r " + self.FrameworkDir + "/includes/ " + self.TargetOutputDir )

	def Save( self, Report, Options ):
		self.TargetOutputDir, self.FrameworkDir, self.Version, self.Release, self.TargetURL, self.HostIP, self.PortNumber, self.TransactionLogHTML, self.AlternativeIPs = self.Core.Config.GetAsList( ['OUTPUT_PATH', 'FRAMEWORK_DIR', 'VERSION', 'RELEASE', 'TARGET_URL', 'HOST_IP', 'PORT_NUMBER', 'TRANSACTION_LOG_HTML', 'ALTERNATIVE_IPS'] )
		self.ReportType = Options['ReportType']
		if not self.Init:
			self.CopyAccessoryFiles()
			self.Init = True # The report is re-generated several times, this ensures images, stylesheets, etc are only copied once at the start
		with open( self.Core.Config.Get( Report ), 'w' ) as file:
			template = self.Template_env.get_template( 'header.html' )

			vars = {
						"Title" : Options['Title'],
						"ReportType" : Options['ReportType'],
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
						"AuxPluginsTypes": self.Core.Config.Plugin.GetTypesForGroup( 'aux' ),
						"WebTestGroups":self.Core.Config.Plugin.GetWebTestGroups(),
						"Logs": {
								 "Errors": {
											  "nb": self.Core.DB.GetLength( 'ERROR_DB' ),
											  "link":  str( self.Core.Config.GetAsPartialPath( 'ERROR_DB' ) )
											},
							    "Unreachables": {
											  "nb": self.Core.DB.GetLength( 'UNREACHABLE_DB' ),
											  "link":  str( self.Core.Config.GetAsPartialPath( 'UNREACHABLE_DB' ) ) ,
												 },
							    "Transaction_Log_HTML": {
													"link": self.Core.Config.GetAsPartialPath( 'TRANSACTION_LOG_HTML' ),
													},
						    	"All_Downloaded_Files": {
													"link": '#',
													},
							    "All_Transactions": {
													"link": self.Core.Config.GetAsPartialPath( 'TRANSACTION_LOG_TRANSACTIONS' ),
													},
								"All_Requests": {
													"link": self.Core.Config.GetAsPartialPath( 'TRANSACTION_LOG_REQUESTS' ),
													},
								"All_Response_Headers": {
													"link": self.Core.Config.GetAsPartialPath( 'TRANSACTION_LOG_RESPONSE_HEADERS' ),
													},
								"All_Response_Bodies": {
													"link": self.Core.Config.GetAsPartialPath( 'TRANSACTION_LOG_RESPONSE_BODIES' ),
													},
							      },
						"Urls":  {
								    "All_URLs_link": self.Core.Config.GetAsPartialPath( 'ALL_URLS_DB' ),
							    	"File_URLs_link": self.Core.Config.GetAsPartialPath( 'FILE_URLS_DB' ),
								    "Fuzzable_URLs_link": self.Core.Config.GetAsPartialPath( 'FUZZABLE_URLS_DB' ),
									"Image_URLs_link":  self.Core.Config.GetAsPartialPath( 'IMAGE_URLS_DB' ),
									"Error_URLs_link": self.Core.Config.GetAsPartialPath( 'ERROR_URLS_DB' ),
									"External_URLs_link":  self.Core.Config.GetAsPartialPath( 'EXTERNAL_URLS_DB' ),
									},
						"Urls_Potential":  {
								    "All_URLs_link": self.Core.Config.GetAsPartialPath( 'POTENTIAL_ALL_URLS_DB' ),
							    	"File_URLs_link": self.Core.Config.GetAsPartialPath( 'POTENTIAL_FILE_URLS_DB' ),
								    "Fuzzable_URLs_link": self.Core.Config.GetAsPartialPath( 'POTENTIAL_FUZZABLE_URLS_DB' ),
									"Image_URLs_link":  self.Core.Config.GetAsPartialPath( 'POTENTIAL_IMAGE_URLS_DB' ),
									"Error_URLs_link": self.Core.Config.GetAsPartialPath( 'POTENTIAL_ERROR_URLS_DB' ),
									"External_URLs_link":  self.Core.Config.GetAsPartialPath( 'POTENTIAL_EXTERNAL_URLS_DB' ),
									},
					}

			file.write( template.render( vars ) )
