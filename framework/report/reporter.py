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
from framework.report.html import renderer
from framework.report.html.filter import sanitiser
from framework.report import header, summary
from collections import defaultdict

PLUGIN_DELIM = '__' # Characters like ; | . or / trip CKEditor as separators
REPORT_PREFIX = '__rep__'

class Reporter:
	def __init__( self, CoreObj ):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False
		self.Render = renderer.HTMLRenderer( self.Core )
		self.Header = header.Header( self.Core )
		self.Summary = summary.Summary( self.Core )
		self.Sanitiser = sanitiser.HTMLSanitiser()
		self.PluginDivIds = {}
		self.CounterList = []

        def DrawImageFromConfigPair( self, ConfigList ):
                FileName, ToolTip = self.Core.Config.GetAsList( ConfigList )
                template = Template( """
                		<img src="images/{{ FileName }}.png" title="{{ ToolTip }}">
                """ )
                vars = {
						"FileName" : FileName,
						"ToolTip": ToolTip
						}
                return template.render( vars )

	def GetPluginDelim( self ):
		return PLUGIN_DELIM

        def GetPluginDivId( self, Plugin ):
                # "Compression" attempt while keeping uniqueness:
                # First letter from plugin type is enough to make plugin div ids unique and predictable
                #return MultipleReplace(Code, { 'OWASP' : 'O', 'OWTF' : 'F', '-' : '', '0' : '' })+PluginType[0]
                return self.GetPluginDelim().join( [ Plugin['Group'], Plugin['Type'], Plugin['Code'] ] ) # Need this info for fast filtering in JS

        def DrawCommand( self, Command ):
                #cgi.escape(MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict()))
                return cgi.escape( Command )#.replace(';', '<br />') -> Sometimes ";" encountered in UA, cannot do this and it is not as helpful anyway

        def DrawCommandTable( self, Command ):
                Table = self.Render.CreateTable( {'class' : 'run_log'} )
                Table.CreateRow( [ 'Analysis Command' ], True )
                Table.CreateRow( [ self.DrawCommand( Command ) ] )
                return Table.Render()

        def DrawTransacLinksStr( self, PathList, ToFile = True ):
                URL, TransacPath, ReqPath, ResHeadersPath, ResBodyPath = PathList
                LinksStr = self.Render.DrawButtonLink( 'Site', URL ) + " "
                LinksStr += " ".join( self.Render.DrawLinkPairs( [['F', TransacPath ], ['R', ReqPath], ['H', ResHeadersPath], ['B', ResBodyPath]], 'DrawButtonLink', {}, ToFile ) )
                return LinksStr

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
                        template = Template( """
                        	<h4 id="h{{ DivId }}"><u> {{ Plugin['Title'] }} </u> - <i> {{ Plugin['Type']|replace( '_', ' ' )|upper }} </i>
                            &nbsp;&nbsp;
                            <div style="display:inline;{% if 'Counters' not in Options %}float:right;{% endif %}">
								<table class="counter"> 
									<tr>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="ToggleNotesBox('{{ DivId }}')" id="{{ DivId }}lamp_active" >
																<span> <img src="images/lamp_active.png" title="Hide/Show Notes Box"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="MarkAsSeen('{{ DivId }}')" id="l{{ DivId }}" >
																<span> <img src="images/pencil.png" title="Strike-through"> </span>
																	</a>
																</td>
														
																<td>
																<a href="javascript:void(0);" class="icon"  onclick="Rate('{{ DivId }}','attention_orange', this)" id="{{ DivId }}attention_orange">
																<span> <img src="images/attention_orange.png" title="Warning"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon"  onclick="Rate('{{ DivID }}','bonus_red', this)"  id="{{ DivID }}bonus_red">
																<span> <img src="images/bonus_red.png" title="Exploitable"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','star_3', this)"  id='{{ DivID }}star_3'>
																<span> <img src="images/star_3.png" title="Brief look (no analysis)"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','star_3', this)" id="{{ DivID }}star_2">
																<span> <img src="images/star_2.png" title="Initial look (analysis incomplete)"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon"  onclick="Rate('{{ DivID }}','check_green', this)" id="{{ DivID }}check_green">
																<span> 
																	<img src="images/check_green.png" title="Test Passed"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','bug', this)" id="{{ DivID }}bug">
																<span> <img src="images/bug.png" title="Functional/Business Logic bug"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','flag_blue', this)" id="{{ DivID }}flag_blue">
																<span> <img src="images/flag_blue.png" title="Low Severity"> </span>
																	</a>
																</td>
						
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','flag_yellow', this)" id="{{ DivID }}flag_yellow">
																<span> <img src="images/flag_yellow.png" title="Medium Severity"> </span>
																	</a>
																</td>
						
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','flag_red', this)" id="{{ DivID }}flag_red">
																<span> <img src="images/flag_red.png" title="High Severity"> </span>
																	</a>
																</td>
																<td>
																	<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','flag_violet', this)" id="{{ DivID }}flag_violet">
																		<span> <img src="images/flag_violet.png" title="Critical Severity"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="Rate('{{ DivID }}','delete', this)" id="{{ DivID }}delete">
																<span> <img src="images/delete.png" title="Remove Flag"> </span>
																	</a>
																</td>
																<td>
																<a href="javascript:void(0);" class="icon" onclick="HidePlugin('{{ DivId }}')" id="{{ DivID }}options">
																<span> <img src="images/arrow_up.png" title="Close Plugin Report"> </span>
																	</a>
																</td>
															</tr>
													</table>
											</div>
													<div id='advanced_filter_options' style='display: none;'>
													<h4>Filter Options</h4><p>Tip: Hold the Ctrl key while selecting or unselecting for multiple choices.<br />NOTE: Clicking on any filter will apply these options from now on. Options will survive a screen refresh</p>
													<table class="transaction_log"> 
																			<tr>
																				<th>Plugin Groups</th>
																				<th>Web Plugin Types</th>
																				<th>Aux Plugin Types</th>
																			</tr>
																			<tr>
																				<td>
																						<select multiple='multiple'  id='SelectPluginGroup' onchange='SetSelectFilterOptions(this)'> 
																							{% for Value in PluginTypes %}
																								<option value="{{ Value }}"> 
																									{{ Value|e }}
																								 </option>
																							{% endfor %}
																						</select>
																						
																				</td>
																				<td>
																						<select multiple='multiple'  id='SelectPluginTypesWeb' size='6' onchange='SetSelectFilterOptions(this)'> 
																							{% for Value in WebPluginTypes %}
																								<option value="{{ Value }}"> 
																									{{ Value|e }}
																								 </option>
																							{% endfor %}
																						</select>
																				</td>
																				<td>
																					<select multiple='multiple'  id='SelectPluginTypesAux' size='6' onchange='SetSelectFilterOptions(this)'> 
																							{% for Value in AuxPluginsTypes %}
																								<option value="{{ Value }}"> 
																									{{ Value|e }}
																								 </option>
																							{% endfor %}
																						</select>
																				</td>
																			</tr>
																		</table>
																		<table class="transaction_log"> 
																			<tr>
																				<th>Web Test Groups</th>
																			</tr>
																			<tr>
																				<td>
																					<select multiple='multiple'  id='SelectWebTestGroups' size='10' onchange='SetSelectFilterOptions(this)'> 
																							{% for Item in WebTestGroups %}
																								<option value="{{ Item["Code"] }}"> 
																									{{ Item["Code"] }} - {{ Item["Descript"] }} - {{ Item["Hint"] }} 
																								 </option>
																							{% endfor %}
																						</select>
																				</td>
																			</tr>
													</table>
													</div>

									
						<table class="report_intro"> 
                        		<tr>
                        			<th>Plugin</th>
                        			<th>Start</th>
                        			<th>End</th>
                        			<th>Runtime</th>
                        			<th>Output Files</th>
                        		</tr>
                        		<tr>
                        			<td>{{ Plugin['Type'] }}/{{ Plugin['File'] }}</td>
                        			<td>{{ Plugin['Start'] }}</td>
                        			<td>{{ Plugin['End'] }}</td>
                        			<td>{{ Plugin['RunTime'] }}</td>
                        			<td>
	                        			<a href="SAVE_DIR" class="button" target="_blank">
											<span> Browse </span>
										</a>
									</td>
                        		</tr>

						</table>
						{# Generate unique id every time to detect if plugin report changed to highlight modified stuff without losing review data (i.e. same plugin id) #}
						<div id='token_{{ DivId }}' style='display: none;'> {{ NextHTMLID }} </div>
                        <div>
							<table class="transaction_log">
								<tr>
									<th> Notes </th>
								</tr>
								<tr>
									<td> 
										<div id="note_preview_{{ DivId }}"></div>
										<div style="float: right;">
											<a href="javascript:ToggleNotesBox('{{ DivId }}')">Edit</a>
										</div>
										<div id="notes_{{ DivId }}" style="display: none;">
											<!-- autocomplete must be off because otherwise you see the text but is not saved in the review at all, which is counter-intuitive -->
											<textarea id="note_text_{{ DivId }}" autocomplete="off" rows=15 cols=150></textarea> 
										</div>
									</td>
								</tr>
							</table>
							   </div>
						<hr />
                            {{ HTMLtext }}
                         </div>
                     
                        	""" )
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
		template = Template( """
		<table class='transactions'>
				<tr><th colspan="2" align="center">HTTP Transactions</th></tr>
				<tr><th> Request </th><th> Response </th></tr>
				{% for Transaction in TransactionList %}
					<tr> 
						<td class="alt"> 
							{{ Transaction.HTMLLink }} ( {{ Transaction.TimeHuman }} ) 
							{{ Transaction.LinksForID }}
							 <br /> 
							<pre> {{ Transaction.RawRequest|e|slice(NumLinesReq) }} </pre>
						 </td>
						<td><pre> {{ Transaction.RawResponse|e|slice(NumLinesRes) }} </pre> </td> 
					</tr>
				{% endfor %}
		</table>
		""" )

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

	def GetTransactionLink( self, TransacPath ):
		return "/".join( TransacPath.split( "/" )[-5:] )

        def GetIconInfoAsStr( self, InfoList ):
                FileName, Title = self.Core.Config.GetAsList( InfoList )
                return FileName + '@' + Title

        def GetIconInfoPairsAsStrList( self, IconInfoPairs ):
                InfoList = []
                for IconInfoList in IconInfoPairs:
                        InfoList.append( self.GetIconInfoAsStr( IconInfoList ) )
                return InfoList

        def ReportStart( self ):
		self.CounterList = []
		ReportType = self.Core.Config.Get( 'REPORT_TYPE' )
		self.Header.Save( 'HTML_DETAILED_REPORT_PATH', { 'ReportType' : ReportType, 'Title' :  ReportType + " Report" } )

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
			TestGroups.append( {
'TestGroupHeaderStr' : '<div id="' + TestGroup['Code'] + '" class="testgroup">' + self.Render.DrawButtonLink( TestGroup['Descrip'] + " (" + TestGroup['Code'] + ")", TestGroup['URL'], { 'class' : 'report_index' } ) + "&nbsp;" + TestGroup['Hint']
, 'RegisteredPlugins' : RegisteredPluginList } )
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
			TestGroups.append( {
'TestGroupHeaderStr' : '<div id="' + TestGroup['Code'] + '" class="testgroup">' + self.Render.DrawButtonLink( TestGroup['Descrip'] + " (" + TestGroup['Code'] + ")", TestGroup['URL'], { 'class' : 'report_index' } ) + "&nbsp;" + TestGroup['Hint']
, 'RegisteredPlugins' : RegisteredPluginList } )
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
'TestGroupHeaderStr' : '<div id="' + PluginType.lower() + '"><br />' + self.Render.DrawButtonLink( PluginType.upper(), '#', { 'class' : 'report_index' } ) + "&nbsp;" # No hint ..
, 'RegisteredPlugins' : RegisteredPluginList } )
		return TestGroups

	def GetTestGroups( self, ReportType ):

		if ReportType == 'URL':
			return self.GetRegisteredWebPlugins( ReportType )
		elif ReportType == 'AUX':
			return self.GetRegisteredAuxPlugins( ReportType )
		elif ReportType == 'NET':
			return self.GetRegisteredNetPlugins( ReportType )


	def DrawReportSkeleton( self ): # Create Div + Tab structure for Review + Report ease of navigation
		template = Template( """	
		<div id="generated_report" class="generated_report" style="display:none;">
			<div id='{{ REPORT_PREFIX }}intro'></div>
				<ul id="tabs">
					<li>
						<a href="javascript:void(0);" id="tab_{{ REPORT_PREFIX }}stats" target=""
								onclick="SetClassNameToElems(new Array('tab_{{ REPORT_PREFIX }}stats,tab_{{ REPORT_PREFIX }}passed, tab_{{ REPORT_PREFIX }}findings, tab_{{ REPORT_PREFIX }}unrated'), '');
										 HideDivs(new Array('{{ REPORT_PREFIX }}stats,{{ REPORT_PREFIX }}passed, {{ REPORT_PREFIX }}findings, {{ REPORT_PREFIX }}unrated'));
										 this.className = 'selected'; 
										 ToggleDiv('{{ REPORT_PREFIX }}stats');" >
							Statistics
						</a>
				 </li>
				 <li>
						<a href="javascript:void(0);" id="tab_{{ REPORT_PREFIX }}passed" target=""
								onclick="SetClassNameToElems(new Array('tab_{{ REPORT_PREFIX }}stats,tab_{{ REPORT_PREFIX }}passed, tab_{{ REPORT_PREFIX }}findings, tab_{{ REPORT_PREFIX }}unrated'), '');
										 HideDivs(new Array('{{ REPORT_PREFIX }}stats,{{ REPORT_PREFIX }}passed, {{ REPORT_PREFIX }}findings, {{ REPORT_PREFIX }}unrated'));
										 this.className = 'selected'; 
										 ToggleDiv('{{ REPORT_PREFIX }}stats');" >
							Passed Tests
						</a>
				 </li>
				 <li>
						<a href="javascript:void(0);" id="tab_{{ REPORT_PREFIX }}findings" target=""
								onclick="SetClassNameToElems(new Array('tab_{{ REPORT_PREFIX }}stats,tab_{{ REPORT_PREFIX }}passed, tab_{{ REPORT_PREFIX }}findings, tab_{{ REPORT_PREFIX }}unrated'), '');
										 HideDivs(new Array('{{ REPORT_PREFIX }}stats,{{ REPORT_PREFIX }}passed, {{ REPORT_PREFIX }}findings, {{ REPORT_PREFIX }}unrated'));
										 this.className = 'selected'; 
										 ToggleDiv('{{ REPORT_PREFIX }}stats');" >
							Findings
						</a>
				 </li>
				 <li>
						<a href="javascript:void(0);" id="tab_{{ REPORT_PREFIX }}unrated" target=""
								onclick="SetClassNameToElems(new Array('tab_{{ REPORT_PREFIX }}stats,tab_{{ REPORT_PREFIX }}passed, tab_{{ REPORT_PREFIX }}findings, tab_{{ REPORT_PREFIX }}unrated'), '');
										 HideDivs(new Array('{{ REPORT_PREFIX }}stats,{{ REPORT_PREFIX }}passed, {{ REPORT_PREFIX }}findings, {{ REPORT_PREFIX }}unrated'));
										 this.className = 'selected'; 
										 ToggleDiv('{{ REPORT_PREFIX }}stats');" >
							Not Rated
						</a>
				 </li>
				<li class="icon">
						<a href="javascript:void(0);" class="icon" onclick="ShowDivs(new Array('{{ DivIdList|join("','") }}'));SetClassNameToElems(new Array('%(TabIdList)s'), '');">
							<span>
								<img src="images/{{ FIXED_ICON_EXPAND_PLUGINS }}.png" title="{{ NAV_TOOLTIP_EXPAND_PLUGINS }}">&nbsp; 
							</span>
						</a>	
						&nbsp;
						<a href="javascript:void(0);" class="icon" onclick="HideDivs(new Array('{{ DivIdList|join("','") }}'));SetClassNameToElems(new Array('%(TabIdList)s'), '');">
							<span>
								<img src="images/{{ FIXED_ICON_CLOSE_PLUGINS }}.png" title="{{ NAV_TOOLTIP_CLOSE_PLUGINS }}">&nbsp; 
							</span>
						</a>
						&nbsp;	
						<a href="javascript:void(0);" class="icon_unfilter"  style='display: none;' onclick="SetClassNameToElems(new Array('%(TabIdList)s'), '');UnfilterBrotherTabs(this);">
							<span>
								<img src="images/{{ FIXED_ICON_PLUGIN_INFO }}.png" title="{{ NAV_TOOLTIP_CLOSE_PLUGINS }}">&nbsp; 
							</span>
						</a>
				</li>
				</ul>
				<!-- Div Content -->
			</div>
		<div id="review_content" class="review_content">

		"""
			% {
				"DivIdList" : "{{ REPORT_PREFIX }}stats,{{ REPORT_PREFIX }}passed, {{ REPORT_PREFIX }}findings, {{ REPORT_PREFIX }}unrated",
				"TabIdList" : "tab_{{ REPORT_PREFIX }}stats,tab_{{ REPORT_PREFIX }}passed, tab_{{ REPORT_PREFIX }}findings, tab_{{ REPORT_PREFIX }}unrated"
				}

		 )

		vars = {
					"REPORT_PREFIX" : REPORT_PREFIX,
					"FIXED_ICON_EXPAND_PLUGINS" : self.Core.Config.Get( 'FIXED_ICON_EXPAND_PLUGINS' ),
					"NAV_TOOLTIP_EXPAND_PLUGINS" : self.Core.Config.Get( 'NAV_TOOLTIP_EXPAND_PLUGINS' ),
					"FIXED_ICON_CLOSE_PLUGINS" : self.Core.Config.Get( 'FIXED_ICON_CLOSE_PLUGINS' ),
					"NAV_TOOLTIP_CLOSE_PLUGINS" : self.Core.Config.Get( 'NAV_TOOLTIP_CLOSE_PLUGINS' ),
					"FIXED_ICON_PLUGIN_INFO" : self.Core.Config.Get( 'FIXED_ICON_PLUGIN_INFO' ),
					"FILTER_TOOLTIP_INFO_UNFILTER" : self.Core.Config.Get( 'FILTER_TOOLTIP_INFO_UNFILTER' ),
				}

		return template.render( vars )

	def ReportFinish( self ): # Group all partial reports (whether done before or now) into the final report
		Target = self.Core.Config.GetTarget()
		NumPluginsForTarget = self.Core.DB.PluginRegister.NumPluginsForTarget( Target )
		template = Template( """
		{% if NumPluginsForTarget %}
		
		
		{% endif %}
		""" )
		if not NumPluginsForTarget > 0:
			cprint( "No plugins completed for target, cannot generate report" )
			return None # Must abort here, before report is generated
		self.ReportStart() # Wipe report
		with open( self.Core.Config.Get( 'HTML_DETAILED_REPORT_PATH' ), 'a' ) as file:
			file.write( '<div id="GlobalReportButtonsTop" style="display:none;"></div>' + self.DrawReportSkeleton() ) # Start OWASP Testing Guide Item List
			AllPluginsTabIdList = []
			AllPluginsDivIdList = []
			AllCodes = []
			for TestGroup in self.GetTestGroups( self.Core.Config.Get( 'REPORT_TYPE' ) ):
				HeaderStr = TestGroup['TestGroupHeaderStr']
				Tabs = self.Render.CreateTabs()

				for Match in  TestGroup['RegisteredPlugins']:
					if Match['Code'] not in AllCodes:
						AllCodes.append( Match['Code'] )
					#PluginType = Match['Type']
					#DivId = self.GetPluginDivId(Match['Code'], PluginType)
					DivId = self.GetPluginDivId( Match )
					Tabs.AddDiv( DivId, Match['Label'], open( Match['Path'] ).read() )
					AllPluginsTabIdList.append( "tab_" + DivId )
					AllPluginsDivIdList.append( DivId )
				if Tabs.GetNumDivs() > 0:
					Tabs.CreateCustomTab( 'Results:' ) # First create custom tab, without javascript
					Tabs.CreateTabs() # Create the hide/show deal tabs
					Tabs.CreateTabButtons() # Add handy tab navigation buttons to the right
					HeaderStr += "&nbsp;" * 1 + ( "&nbsp;" * 1 ).join( self.Render.DrawLinkPairs( [ [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_EXPAND_REPORT', 'NAV_TOOLTIP_EXPAND_REPORT' ] ), "ClickLinkById('expand_report')" ], [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_CLOSE_REPORT', 'NAV_TOOLTIP_CLOSE_REPORT' ] ), "ClickLinkById('collapse_report')" ] ], 'DrawButtonJSLink', { 'class' : 'icon' } ) )
				#HeaderStr += "<br />"
       				file.write( HeaderStr + Tabs.Render() + "</div>" ) # Save plugin reports in OWASP Guide order => 1 write per item = less memory-intensive
			if len( AllPluginsTabIdList ) == 0:
				cprint( "ERROR: No plugins found, cannot write report" )
				return None # No plugins found (should not happe)
			template = Template( """
							<br />
							<div id='GlobalReportButtonsBottom' style='display:none;'>
								<a id="expand_report" href="javascript:void(0);" class="button" onclick="SetClassNameToElems(new Array('{{ AllPluginsTabIdList|join("','") }}'), ''); ShowDivs(new Array('{{ AllPluginsDivIdList|join("','") }}'))">
									<span> + </span>
								</a>
								<a id="collapse_report" href="javascript:void(0);" class="button" onclick="SetClassNameToElems(new Array('{{ AllPluginsTabIdList|join("','") }}'), ''); HideDivs(new Array('{{ AllPluginsDivIdList|join("','") }}'))">
									<span> - </span>
								</a>
							</div>
							<script>
								var AllPlugins = new Array('{{ AllPluginsDivIdList|join("','") }}')
								var AllCodes = new Array('{{ AllCodes|join("','") }}')
								var Offset = '{{ REVIEW_OFFSET }}'
								var AllCounters = new Array('filtermatches_counter','filterinfo_counter','filterno_flag_counter','filterunseen_counter','filterseen_counter','filternotes_counter','filterattention_orange_counter','filterbonus_red_counter','filterstar_3_counter','filterstar_2_counter','filtercheck_green_counter','filterbug_counter','filterflag_blue_counter','filterflag_yellow_counter','filterflag_red_counter','filterflag_violet_counter','filterdelete_counter','filteroptions_counter','filterrefresh_counter')
								var DetailedReport = true
								var PluginDelim = '{{ PLUGIN_DELIM }}'
								var ReportMode = false
								var REPORT_PREFIX = '{{ REPORT_PREFIX }}'
							</script>
						</body></html>
			""" )

			vars = {
						"AllPluginsTabIdList" : AllPluginsTabIdList,
						"AllPluginsDivIdList" : AllPluginsDivIdList,
						"AllCodes" : AllCodes,
						"REVIEW_OFFSET" : self.Core.Config.Get( 'REVIEW_OFFSET' ),
						"PLUGIN_DELIM" : PLUGIN_DELIM,
						"REPORT_PREFIX"  : REPORT_PREFIX ,
					}

			file.write( template.render( vars ) ) # Closing HTML Report
			cprint( "Report written to: " + self.Core.Config.Get( 'HTML_DETAILED_REPORT_PATH' ) )
			self.Core.DB.ReportRegister.Add( self.Core.Config.GetAsList( [ 'REVIEW_OFFSET', 'SUMMARY_HOST_IP', 'SUMMARY_PORT_NUMBER', 'HTML_DETAILED_REPORT_PATH', 'REPORT_TYPE' ] ) ) # Register report
			self.Summary.ReportFinish() # Build summary report


        def ReportWrite( self, html, text ):
                cprint( text ) # Text displayed on console only, html saved in report
                with open( self.Core.Config.Get( 'HTML_DETAILED_REPORT_PATH' ), 'a' ) as file:
                        file.write( html ) # Closing HTML Report
