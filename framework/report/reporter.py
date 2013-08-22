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

import cgi
from jinja2 import Template
from jinja2 import Environment, PackageLoader
from framework.lib.general import *
from framework.report.html import renderer
from framework.report.html.filter import sanitiser
from framework.report import summary
from collections import defaultdict
import logging
import time

PLUGIN_DELIM = '__' # Characters like ; | . or / trip CKEditor as separators
REPORT_PREFIX = '__rep__'

class Reporter:
	def __init__( self, CoreObj ):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False
		self.Render = renderer.HTMLRenderer( self.Core )
		self.Summary = summary.Summary( self.Core )
		self.Sanitiser = sanitiser.HTMLSanitiser()
		self.PluginDivIds = {}
		self.CounterList = []
		self.Template_env = env = Environment( loader = PackageLoader( 'framework.report', 'templates' ) )


	def GetPluginDelim( self ):
		return PLUGIN_DELIM

	def CopyAccessoryFiles( self ):
		TargetOutputDir = self.Core.Config.Get( 'OUTPUT_PATH' )
		FrameworkDir = self.Core.Config.Get( 'FRAMEWORK_DIR' )
		Log( "Copying report images .." )
		self.Core.Shell.shell_exec( "cp -r " + FrameworkDir + "/images/ " + TargetOutputDir )
		Log( "Copying report includes (stylesheet + javascript files).." )
		self.Core.Shell.shell_exec( "cp -r " + FrameworkDir + "/includes/ " + TargetOutputDir )

        def GetPluginDivId( self, Plugin ):
                # "Compression" attempt while keeping uniqueness:
                # First letter from plugin type is enough to make plugin div ids unique and predictable
                #return MultipleReplace(Code, { 'OWASP' : 'O', 'OWTF' : 'F', '-' : '', '0' : '' })+PluginType[0]
                return self.GetPluginDelim().join( [ Plugin['Group'], Plugin['Type'], Plugin['Code'] ] ) # Need this info for fast filtering in JS

        def DrawCommand( self, Command ):
                #cgi.escape(MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict()))
                return cgi.escape( Command )#.replace(';', '<br />') -> Sometimes ";" encountered in UA, cannot do this and it is not as helpful anyway

        def DrawTransacLinksStr( self, PathList, ToFile = True ):
                URL, TransacPath, ReqPath, ResHeadersPath, ResBodyPath = PathList
                template = Template( """
                			<!-- Start Transactions Links -->
	                			<a href="{{ Transaction_URL }}" class="button" target="_blank">
									<span> Site </span>
								</a><br />
								<a href="{{ Transaction_Path }}" class="button" target="_blank">
									<span> F </span>
								</a><br />
								<a href="{{ Request_Path }}" class="button" target="_blank">
									<span> R </span>
								</a><br />
								<a href="{{ Resource_Headers_Path }}" class="button" target="_blank">
									<span> H </span>
								</a><br />
								<a href="{{ Resource_Body_Path }}" class="button" target="_blank">
									<span> B </span>
								</a><br />
							<!-- End Transactions Links -->
                			""" )
                vars = {
							"Transaction_URL": URL,
							"Transaction_Path":  TransacPath,
							"Request_Path": ReqPath,
							"Resource_Headers_Path": ResHeadersPath ,
							"Resource_Body_Path": ResBodyPath,
						}

                return template.render( vars )

        def DrawTransacLinksForID( self, ID, ForPlugin = False ):
                PathList = self.Core.DB.Transaction.GetTransactionPathsForID( ID ) # Returns the URL and Transaction Paths for a given Transaction ID
		CleanPathList = [PathList[0]] # Leave URL unmodified
		if ForPlugin:
			for Path in PathList[1:]:#Skip URL, process rest of items in list = File paths
				CleanPathList.append( '../../../' + Path )
		else:
			CleanPathList = PathList
                return self.DrawTransacLinksStr( CleanPathList )

        def SavePluginReport( self, HTMLtext, Plugin ):
                save_dir = self.Core.PluginHandler.GetPluginOutputDir( Plugin )
                if HTMLtext == None:
                        HTMLtext = cprint( "PLUGIN BUG!!: on: " + PluginType.strip() + "/" + PluginFile.strip() + " no content returned" )
                DivId = self.GetPluginDivId( Plugin )
                PluginReportPath = save_dir + "report.html"
                self.Core.CreateMissingDirs( save_dir )
                with open( PluginReportPath, 'w' ) as file: # 'w' is important to overwrite the partial report, necesary for scanners
                        Plugin['RunTime'] = self.Core.Timer.GetElapsedTimeAsStr( 'Plugin' )
                        Plugin['End'] = self.Core.Timer.GetEndDateTimeAsStr( 'Plugin' )
                        template = self.Template_env.get_template( 'plugin_report.html' )
                        vars = {
								"DivId": DivId,
								"SAVE_DIR": self.Core.GetPartialPath( save_dir ),
								"NextHTMLID": self.Core.DB.GetNextHTMLID(),
								"Plugin": Plugin,
								"HTMLtext": unicode( HTMLtext, "utf-8" ) if HTMLtext.__class__ is not unicode else HTMLtext,
								"PluginTypes": self.Core.Config.Plugin.GetAllGroups(),
								"WebPluginTypes": self.Core.Config.Plugin.GetTypesForGroup( 'web' ),
								"AuxPluginsTypes": self.Core.Config.Plugin.GetTypesForGroup( 'aux' ),
								"WebTestGroups":self.Core.Config.Plugin.GetWebTestGroups(),
								}
                        file.write( template.render( vars ) )
		#print "Plugin="+str(Plugin)
		self.Core.DB.PluginRegister.Add( Plugin, PluginReportPath, self.Core.Config.GetTarget() )
                #self.RegisterPartialReport(PluginReportPath) # Partial report saved ok, register partial report in register file for grouping later
                self.ReportFinish() # Provide a full partial report at the end of each plugin

	def DrawHTTPTransactionTable( self, TransactionList, NumLinesReq = 15, NumLinesRes = 15 ): # Draws a table of HTTP Transactions
		template = self.Template_env.get_template( 'http_transaction_table.html' )

		vars = { "NumLinesReq":  NumLinesReq,
				 "NumLinesRes": NumLinesRes,
				"TransactionList":[
								{
									"HTMLLink": unicode( Transaction.HTMLLinkToID.replace( '@@@PLACE_HOLDER@@@', "See Transaction " + Transaction.ID ) ),
							        "TimeHuman":  unicode( Transaction.TimeHuman ),
							        "LinksForID":  unicode( self.DrawTransacLinksForID( Transaction.ID ) ),
								    "RawRequest":  unicode( Transaction.GetRawRequest() ),
								    "RawResponse":  unicode( Transaction.GetRawResponse()  , "utf-8" ),
								} for Transaction in TransactionList
								]

			}
		return template.render( vars )



	def GetRegisteredWebPlugins( self, ReportType ): # Web Plugins go in OWASP Testing Guide order
		TestGroups = []
		for TestGroup in self.Core.Config.Plugin.GetWebTestGroups(): #Follow defined web test group order, NOT execution order
			RegisteredPlugins = self.Core.DB.PluginRegister.Search( { 'Code' : TestGroup['Code'], 'Target' : self.Core.Config.GetTarget() } )
			if not RegisteredPlugins:
				continue # The plugin has not been registered yet
			RegisteredPluginList = []
			for Match in RegisteredPlugins:
				Match['Label'] = Match['Type'] # For url plugins the Label is a display of the plugin type (passive, semi_passive, etc)
				RegisteredPluginList.append( Match )

			TestGroups.append( 
								{
								'TestGroupInfo':  TestGroup ,
								 'RegisteredPlugins' : RegisteredPluginList
								 }
							 )
			#'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'"><br />'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
		return TestGroups

	def GetRegisteredNetPlugins( self, ReportType ): # netPlugins go in OWASP Testing Guide order
		TestGroups = []
		for TestGroup in self.Core.Config.Plugin.GetNetTestGroups(): #Follow defined web test group order, NOT execution order
			RegisteredPlugins = self.Core.DB.PluginRegister.Search( { 'Code' : TestGroup['Code'], 'Target' : self.Core.Config.GetTarget() } )
			if not RegisteredPlugins:
				continue # The plugin has not been registered yet
			RegisteredPluginList = []
			for Match in RegisteredPlugins:
				Match['Label'] = Match['Type'] # For url plugins the Label is a display of the plugin type (passive, semi_passive, etc)
				RegisteredPluginList.append( Match )

			TestGroups.append( 
								{
									'TestGroupInfo': TestGroup,
									'RegisteredPlugins' : RegisteredPluginList
								}
							)
			#'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'"><br />'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
		return TestGroups



	def GetRegisteredAuxPlugins( self, ReportType ): # Web Plugins go in OWASP Testing Guide order
		TestGroups = []
		for PluginType in self.Core.Config.Plugin.GetTypesForGroup( 'aux' ): # Report aux plugins in alphabetical order
			RegisteredPlugins = self.Core.DB.PluginRegister.Search( { 'Type' : PluginType, 'Target' : 'aux' } ) # Aux plugins have an aux target
			if not RegisteredPlugins:
				continue # The plugin has not been registered yet
			RegisteredPluginList = []
			for Match in RegisteredPlugins:
				Match['Label'] = Match['Args'] # For aux plugins the Label is a display of the arguments passed
				RegisteredPluginList.append( Match )

			TestGroups.append( {
								'TestGroupInfo': { "PluginType":PluginType },
								'RegisteredPlugins' : RegisteredPluginList
								 }
							 )
		return TestGroups

	def GetTestGroups( self, ReportType ):
		if ReportType == 'URL':
			return self.GetRegisteredWebPlugins( ReportType )
		elif ReportType == 'AUX':
			return self.GetRegisteredAuxPlugins( ReportType )
		elif ReportType == 'NET':
			return self.GetRegisteredNetPlugins( ReportType )


	def ReportFinish( self ): # Group all partial reports (whether done before or now) into the final report
		Target = self.Core.Config.GetTarget()
		NumPluginsForTarget = self.Core.DB.PluginRegister.NumPluginsForTarget( Target )
		if not NumPluginsForTarget > 0:
			Log( "No plugins completed for target, cannot generate report" )
			return None # Must abort here, before report is generated
		#ReportStart -- Wipe report
		self.CounterList = []
		if not self.Init:
			self.CopyAccessoryFiles()
			self.Init = True # The report is re-generated several times, this ensures images, stylesheets, etc are only copied once at the start

		with open( self.Core.Config.Get( 'HTML_DETAILED_REPORT_PATH' ), 'w' ) as file:
			template = self.Template_env.get_template( 'report.html' )

			vars = {

						"ReportType" :  self.Core.Config.Get( 'REPORT_TYPE' ),
						"Title" :  self.Core.Config.Get( 'REPORT_TYPE' ) + " Report",
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
						"Globals": {
									"AllPluginsTabIdList": [
											"tab_" + self.GetPluginDivId( Match )
											 for TestGroup in self.GetTestGroups( self.Core.Config.Get( 'REPORT_TYPE' ) )  for Match in  TestGroup['RegisteredPlugins']
											 ],
									"AllPluginsDivIdList":[
											 self.GetPluginDivId( Match )
											 for TestGroup in self.GetTestGroups( self.Core.Config.Get( 'REPORT_TYPE' ) )  for Match in  TestGroup['RegisteredPlugins']
											 ],
									"AllCodes": [
											 Match['Code'] #eliminate repetitions,
											 for TestGroup in self.GetTestGroups( self.Core.Config.Get( 'REPORT_TYPE' ) )  for Match in  TestGroup['RegisteredPlugins']
											 ],
									},
						"TestGroups": [
									{
										"TestGroupInfo": TestGroup['TestGroupInfo'],
										"Matches" : [
														{
														 "DivId": self.GetPluginDivId( Match ),
														 'TabId': "tab_" + self.GetPluginDivId( Match ),
														 "TabName": Match["Label"],
														 "DivContent": open( Match['Path'] ).read(),
														}
														for Match in TestGroup['RegisteredPlugins']
														],
										 "TabIdList": [
														"tab_" + self.GetPluginDivId( Match )
														for Match in TestGroup['RegisteredPlugins']
														],
										"DivIdList": [
														self.GetPluginDivId( Match )
														for Match in TestGroup['RegisteredPlugins']
														]
									}
									 for TestGroup in self.GetTestGroups( self.Core.Config.Get( 'REPORT_TYPE' ) )
									],
						"REVIEW_OFFSET" : self.Core.Config.Get( 'REVIEW_OFFSET' ),
						"PLUGIN_DELIM" : PLUGIN_DELIM,
						"REPORT_PREFIX"  : REPORT_PREFIX ,
					}



			file.write( template.render( vars ) ) # Closing HTML Report
			Log( "Report written to: " + self.Core.Config.Get( 'HTML_DETAILED_REPORT_PATH' ) )
			self.Core.DB.ReportRegister.Add( self.Core.Config.GetAsList( [ 'REVIEW_OFFSET', 'SUMMARY_HOST_IP', 'SUMMARY_PORT_NUMBER', 'HTML_DETAILED_REPORT_PATH', 'REPORT_TYPE' ] ) ) # Register report
			self.Summary.ReportFinish() # Build summary report
