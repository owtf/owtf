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
from jinja2 import Template
from framework.lib.general import *
from collections import defaultdict

class Header:
	def __init__( self, CoreObj ):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False

        def CopyAccessoryFiles( self ):
                cprint( "Copying report images .." )
                self.Core.Shell.shell_exec( "cp -r " + self.FrameworkDir + "/images/ " + self.TargetOutputDir )
                cprint( "Copying report includes (stylesheet + javascript files).." )
                self.Core.Shell.shell_exec( "cp -r " + self.FrameworkDir + "/includes/ " + self.TargetOutputDir )

        def DrawRunDetailsTable( self ):
                template = Template( """
                <table class="run_log">
					 <tr>
	                	<th colspan="5"> Run Log </th>
	                </tr>
	                <tr> 
						<th> Start </th> 
						<th> End </th> 
						<th> Runtime </th> 
						<th> Command </th> 
						<th> Status </th> 
					</tr>
				{% for Start, End, Runtime, Command, Status in RUN_DB  %}
					<tr> 
						<td> {{ Start }} </td> 
						<td	class="alt"> {{ End }} </td> 
						<td> {{ Runtime }} </td> 
						<td	class="alt"> {{ Command }} </td> 
						<td> {{ Status }} </td> 
					</tr>
				{% endfor %}
				</table>
                """ )
                return template.render( RUN_DB = self.Core.DB.GetData( 'RUN_DB' ) )

        def GetDBButtonLabel( self, LabelStart, RedFound, NormalNotFound, DBName ):
                DBLabel = LabelStart
                if self.Core.DB.GetLength( DBName ) > 0:
                        DBLabel += RedFound
                        DBLabel = "<font color='red'>" + DBLabel + "</font>"
                else:
                        DBLabel += NormalNotFound
                return DBLabel

	def DrawReviewDeleteOptions( self ):
		template = Template ( """
			<a href="javascript:void(0);" class="button" onclick="ClearReview();">
				<span> Delete THIS Review </span>
			</a><br/>
			<a href="javascript:void(0);" class="button" onclick="DeleteStorage();">
				<span> Delete ALL Reviews </span>
			</a>
		""" )
		return template.render()

	def DrawReviewMiscOptions( self ):
		template = Template ( """
			<a href="javascript:void(0);" class="button" onclick="ShowUsedMem();">
				<span> Show Used Memory (KB) </span>
			</a><br/>
			<a href="javascript:void(0);" class="button" onclick="ShowUsedMemPercentage();">
				<span> Show Used Memory (%) </span>
			</a><br/>
			<a href="javascript:void(0);" class="button" onclick="ShowDebugWindow();">
				<span> Show Debug Window </span>
			</a><br/>
			<a href="javascript:void(0);" class="button" onclick="HideDebugWindow();">
				<span> Hide Debug Window </span>
			</a>
		""" )
		return template.render()

	def DrawReviewImportExportOptions( self ):
		template = Template ( """
			<a href="javascript:void(0);" class="button" onclick="ImportReview();">
				<span> Import Review </span>
			</a><br/>
			<a href="javascript:void(0);" class="button" onclick="ExportReviewAsText();">
				<span> Export Review as text </span>
			</a><br/>
			<textarea rows="20" cols="100" id="import_export_box"></textarea>
		""" )
		return template.render()


	def DrawGeneralLogs( self ):
		template = Template ( """

			<a href="{{ Errors.link }}" class="button" target="_blank">
				<span> 
					
					{% if Errors.nb %} 
						<font color='red'>Errors:Found, please report!</font>
					{% else  %}
						Errors: Not found
					{% endif %}
						
			    </span>
			</a><br/>
			<a href="{{ Unreachables.link }}" class="button" target="_blank">
				<span> 
					
					{% if Unreachables.nb %} 
						<font color='red'>Unreachable targets: 'Yes!</font>
					{% else  %}
						Unreachable targets: No
					{% endif %}
						
			    </span>
			</a><br/>
			<a href="{{ Transaction_Log_HTML.link }}" class="button" target="_blank">
				<span> 	Transaction Log (HTML) </span>
			</a><br/>
			<a href="{{ All_Downloaded_Files.link }}" class="button" target="_blank">
				<span> 	All Downloaded Files - To be implemented </span>
			</a><br/>
			<a href="{{ All_Transactions.link }}" class="button" target="_blank">
				<span> All Transactions </span>
			</a><br/>
			<a href="{{ All_Requests.link }}" class="button" target="_blank">
				<span> 	All Requests </span>
			</a><br/>
			<a href="{{ All_Response_Headers.link }}" class="button" target="_blank">
				<span> 	All Response Headers </span>
			</a><br/>
			<a href="{{ All_Response_Bodies.link }}" class="button" target="_blank">
				<span> 	All Response Bodies </span>
			</a>
			
		""" )

		Vars = {
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
			      }
		return template.render( Vars )

	def DrawURLDBs( self, DBPrefix = "" ):
		template = Template ( """
			<a href="{{ All_URLs_link }}" class="button" target="_blank">
				<span> 	All URLs </span>
			</a><br/>
			<a href="{{ File_URLs_link }}" class="button" target="_blank">
				<span> File URLs </span>
			</a><br/>
			<a href="{{ Fuzzable_URLs_link }}" class="button" target="_blank">
				<span> Fuzzable URLs </span>
			</a><br/>
			<a href="{{ Image_URLs_link }}" class="button" target="_blank">
				<span> 	Image URLs </span>
			</a><br/>
			<a href="{{ Error_URLs_link }}" class="button" target="_blank">
				<span> 	Error URLs </span>
			</a><br/>
			<a href="{{ External_URLs_link }}" class="button" target="_blank">
				<span> 	External URLs </span>
			</a>
			
		""" )

		Vars = {
			    "All_URLs_link": self.Core.Config.GetAsPartialPath( DBPrefix + 'ALL_URLS_DB' ),
		    	"File_URLs_link": self.Core.Config.GetAsPartialPath( DBPrefix + 'FILE_URLS_DB' ),
			    "Fuzzable_URLs_link": self.Core.Config.GetAsPartialPath( DBPrefix + 'FUZZABLE_URLS_DB' ),
				"Image_URLs_link":  self.Core.Config.GetAsPartialPath( DBPrefix + 'IMAGE_URLS_DB' ),
				"Error_URLs_link": self.Core.Config.GetAsPartialPath( DBPrefix + 'ERROR_URLS_DB' ),
				"External_URLs_link":  self.Core.Config.GetAsPartialPath( DBPrefix + 'EXTERNAL_URLS_DB' ),
				}
		return template.render( Vars )

        def DrawFilters( self ):
		return self.Core.Reporter.DrawCounters( self.ReportType )

        def AddMiscelaneousTabs( self, Tabs ):
                Tabs.AddCustomDiv( 'Miscelaneous:' ) # First create custom tab, without javascript
                Tabs.AddDiv( 'exploit', 'Exploitation', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList( [ ['Hackvertor', 'http://hackvertor.co.uk/public'] , [ 'Hackarmoury', 'http://hackarmoury.com/' ], ['ExploitDB', 'http://www.exploit-db.com/'] , ['ExploitSearch', 'http://www.exploitsearch.net'], [ 'hackipedia', 'http://www.hakipedia.com/index.php/Hakipedia' ] ], 'DrawButtonLink' ) )
                Tabs.AddDiv( 'methodology', 'Methodology', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList( [ ['OWASP', 'https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents'] , ['Pentest Standard', 'http://www.pentest-standard.org/index.php/Main_Page'], ['OSSTMM', 'http://www.isecom.org/osstmm/'] ], 'DrawButtonLink' ) )
                Tabs.AddDiv( 'calculators', 'Calculators', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList( [ ['CVSS Advanced', 'http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2'] , ['CVSS Normal', 'http://nvd.nist.gov/cvss.cfm?calculator&version=2'] ], 'DrawButtonLink' ) )
                Tabs.AddDiv( 'learn', 'Test/Learn', self.Core.Reporter.Render.DrawLinkPairsAsHTMLList( [ [ 'taddong', 'http://blog.taddong.com/2011/10/hacking-vulnerable-web-applications.html' ], [ 'securitythoughts', 'http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/' ] , [ 'danielmiessler', 'http://danielmiessler.com/projects/webappsec_testing_resources/'] ], 'DrawButtonLink' ) )

	def DrawTop( self, Embed = '' ):
		template = Template( """
					{% if ReportType == "URL" or ReportType == "NET" %}
						<div class="detailed_report" style="display: inline; float:left">
							<div style="display: inline; align: left">
								<table class="report_intro'"> 
									<tr>
										<th> 
									 			<a id="target_url" href="{{ TargetLink }}" class="button" target="_blank">
													<span> {{ TargetLink }} </span>
												</a>
									  	</th>
									  	<td> 
									  			 {{ HostIP|e }}
									  			 {% if AlternativeIPs|count %}
									  			 	[Alternative IPs: AlternativeIPs|join(",")|e]
									  			 {% endif %}
										</td>
										<td> 
												{{ PortNumber|e }} 
										</td>
										<td class="disguise"> 
													&nbsp;
													<a href="javascript:void(0);" class="icon" onclick="ToggleReportMode();">
														<span> 	
															<img src="images/wizard.png" title="Generate Report">
					 									</span>
													</a>
													&nbsp;
													<a href="javascript:void(0);" class="icon" onclick="DetailedReportAnalyse()">
														<span> 	
															<img src="images/search_lense24x24.png" title="Analyse">
					 									</span>
													</a>
													&nbsp;
													<a href="javascript:void(0);" class="icon" onclick="DetailedReportAdjust()">
														<span> 	
															<img src="images/plus_gray24x24.png" title="Expand Report">
					 									</span>
													</a>
													&nbsp;
													<a href="javascript:void(0);" class="icon" onclick="DetailedReportCollapse()">
														<span> 	
															<img src="images/minus_gray24x24.png" title="Close Report">
					 									</span>
													</a>
													&nbsp;
													
										</td>
									</tr>
								</table>
								<div style="position: absolute; top: 6px; right: 6px; float: right;"> {{ Embed  }} </div>
							
							 </div>
								{% if ReportType !="NetMap" %} <div style='display:none;'> {% endif %}
						<div class="iframe_padding"></div>
					{% elif ReportType == 'NetMap' %}
						<div style="display: inline; align: left"> <h2>Summary Report</h2>' </div>
					{% elif ReportType == 'AUX' %}
						<div style="display: inline; align: left"> 
									<h2>Auxiliary Plugins 
										<a href="{{ HTML_REPORT }}" target=''>
											<img src="images/home.png" title="Back to Summary Report">
										</a>
									</h2>
					   </div>
					{% endif %}
						<div style="position: absolute; top: 6px; right: 6px; float: right">
							<table class="report_intro"> 
								<tr>
									<th> Seed </th> 
									<th> Review Size </th> 
									<th> Total Size </th> 
									<th> Version </th> 
									<th> Release </th> 
									<th> Site </th> 
								</tr>	
								<tr>
									<td> <span id="seed"> {{ Seed }} </span></td> 
									<td><div id="js_db_size" style="float:left; display: inline; padding-top: 7px"></div><div style="float:right; inline"> <a href="includes/help/help.html#ReviewSize" target="_blank">
												<img src="images/help.png" title="In Firefox localStorage is configurable: 1) Go to: 'about:config' 2) Search for 'dom.storage.default_quota' (value in KB, see: http://arty.name/localstorage.html)">
									</a>				 </div></td> 
									<td> <div id="total_js_db_size"></div> </td> 
									<td> {{ Version }} </td> 
									<td> {{ Release }} </td> 
									<td> <a href="http://owtf.org" class="button" target="_blank"><span> owtf.org </span></a>			</td> 
								</tr>				
							</table>
						</div>
					{% if ReportType !="NetMap" %} </div> {% endif %}
					{% if ReportType == "URL" or ReportType == "NET" %} </div> {% endif %}
		""" )
		vars = {
					"Seed": self.Core.GetSeed(),
					"Version": self.Version,
					"Release": self.Release,
					"ReportType": self.ReportType,
					"HTML_REPORT":  self.Core.Config.Get( 'HTML_REPORT' ),
					"TargetLink": self.TargetURL,
					"HostIP": self.HostIP,
					"AlternativeIPs": self.AlternativeIPs,
					"PortNumber": self.PortNumber,
					"Embed": Embed,
				}


		return template.render( vars )

        def GetJavaScriptStorage( self ): # Loads the appropriate JavaScript library files depending on the configured JavaScript Storage
                Libraries = []
                for StorageLibrary in self.Core.Config.Get( 'JAVASCRIPT_STORAGE' ).split( ',' ):
                        Libraries.append( '<script type="text/javascript" src="includes/' + StorageLibrary + '"></script>' )
                return "\n".join( Libraries )

	def Save( self, Report, Options ):
		self.TargetOutputDir, self.FrameworkDir, self.Version, self.Release, self.TargetURL, self.HostIP, self.PortNumber, self.TransactionLogHTML, self.AlternativeIPs = self.Core.Config.GetAsList( ['OUTPUT_PATH', 'FRAMEWORK_DIR', 'VERSION', 'RELEASE', 'TARGET_URL', 'HOST_IP', 'PORT_NUMBER', 'TRANSACTION_LOG_HTML', 'ALTERNATIVE_IPS'] )
		self.ReportType = Options['ReportType']
		if not self.Init:
			self.CopyAccessoryFiles()
			self.Init = True # The report is re-generated several times, this ensures images, stylesheets, etc are only copied once at the start
		with open( self.Core.Config.Get( Report ), 'w' ) as file:

			ReviewTabs = self.Core.Reporter.Render.CreateTabs()
			ReviewTabs.AddDiv( 'review_import_export', 'Import/Export', self.DrawReviewImportExportOptions() )
			ReviewTabs.AddDiv( 'review_delete', 'Delete', self.DrawReviewDeleteOptions() )
			ReviewTabs.AddDiv( 'review_miscelaneous', 'Miscelaneous', self.DrawReviewMiscOptions() )
			ReviewTabs.CreateTabs()
			ReviewTabs.CreateTabButtons()

			template = Template( """
			
			
			""" )

			Tabs = self.Core.Reporter.Render.CreateTabs()
			Tabs.AddDiv( 'filter', 'Filter', self.DrawFilters() )
			Tabs.AddDiv( 'review', 'Review', ReviewTabs.Render() )
			Tabs.AddDiv( 'runlog', 'History', self.DrawRunDetailsTable() )

			LogTable = self.Core.Reporter.Render.CreateTable( { 'class' : 'run_log' } )
			LogTable.CreateRow( ['General', 'Verified URLs', 'Potential URLs'], True )
			LogTable.CreateRow( [self.DrawGeneralLogs(), self.DrawURLDBs(), self.DrawURLDBs( "POTENTIAL_" )] )
			Tabs.AddDiv( 'logs', 'Logs', LogTable.Render() )

			BodyAttribsStr = ""
			if self.ReportType == 'NetMap':
				self.AddMiscelaneousTabs( Tabs )
				BodyAttribsStr = ' style="overflow-x:hidden;"'
			Tabs.CreateTabs() # Now create the tabs from Divs Above
			Tabs.CreateTabButtons() # Add navigation buttons to the right
			if self.ReportType != 'NetMap': # Embed tabs in detailed report header
				RenderTopStr = self.DrawTop( Tabs.RenderTabs() ) # Embed Tabs in Top div
				TabsStr = Tabs.RenderDivs() # Render Divs below
			else: # Normal tab render
				RenderTopStr = self.DrawTop()
				TabsStr = Tabs.Render()

			template = Template( """
			<html>
				<head>
					<title> {{ Title }}</title>
					<link rel="stylesheet" href="includes/stylesheet.css" type="text/css">
					<link rel="stylesheet" href="includes/jquery-ui-1.9m6/themes/base/jquery.ui.all.css">
				</head>
			<body {{ BodyAttribsStr }}>
				{{ RenderTopStr }}
				{{ TabsStr }}
					<script type="text/javascript" src="includes/jquery-1.6.4.js"></script>\n
					<script type="text/javascript" src="includes/owtf_general.js"></script>\n
					<script type="text/javascript" src="includes/owtf_review.js"></script>\n
					<script type="text/javascript" src="includes/owtf_filter.js"></script>\n
					<script type="text/javascript" src="includes/owtf_reporting.js"></script>\n
					<script type="text/javascript" src="includes/jsonStringify.js"></script>\n
					<script type="text/javascript" src="includes/ckeditor/ckeditor.js"></script>
					<script type="text/javascript" src="includes/ckeditor/adapters/jquery.js"></script>
					{{ JavaScriptStorage }}
			""" )

			file_content = template.render( 
											Title = Options['Title'],
											BodyAttribsStr = BodyAttribsStr,
											RenderTopStr = RenderTopStr,
											TabsStr = TabsStr,
											JavaScriptStorage = self.GetJavaScriptStorage()
											)

			file.write( file_content )
