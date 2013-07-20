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


	def Save( self, Report, Options ):
		self.TargetOutputDir, self.FrameworkDir, self.Version, self.Release, self.TargetURL, self.HostIP, self.PortNumber, self.TransactionLogHTML, self.AlternativeIPs = self.Core.Config.GetAsList( ['OUTPUT_PATH', 'FRAMEWORK_DIR', 'VERSION', 'RELEASE', 'TARGET_URL', 'HOST_IP', 'PORT_NUMBER', 'TRANSACTION_LOG_HTML', 'ALTERNATIVE_IPS'] )
		self.ReportType = Options['ReportType']
		if not self.Init:
			self.CopyAccessoryFiles()
			self.Init = True # The report is re-generated several times, this ensures images, stylesheets, etc are only copied once at the start
		with open( self.Core.Config.Get( Report ), 'w' ) as file:
			Tabs_template = Template( """
			<ul id="tabs">
				<li>
						<a href="javascript:void(0);" id="tab_filter" 
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs'{% if ReportType == 'NetMap' %},'tab_exploit','tab_methodology','tab_calculators','tab_learn'{% endif %}), '');
										 HideDivs(new Array('filter','review','runlog','logs'{% if ReportType == 'NetMap' %},'exploit', 'methodology','calculators','learn'{% endif %}));
										 this.className = 'selected'; 
										 ToggleDiv('filter');" >
							Filter
						</a>
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_review" 
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs'{% if ReportType == 'NetMap' %},'tab_exploit','tab_methodology','tab_calculators','tab_learn'{% endif %}), '');
										 HideDivs(new Array('filter','review','runlog','logs'{% if ReportType == 'NetMap' %},'exploit', 'methodology','calculators','learn'{% endif %}));
										 this.className = 'selected'; 
										 ToggleDiv('review');" >
							Review
						</a>
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_runlog" 
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs'{% if ReportType == 'NetMap' %},'tab_exploit','tab_methodology','tab_calculators','tab_learn'{% endif %}), '');
										 HideDivs(new Array('filter','review','runlog','logs'{% if ReportType == 'NetMap' %},'exploit', 'methodology','calculators','learn'{% endif %}));
										 this.className = 'selected'; 
										 ToggleDiv('runlog');" >
							History
						</a>
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_logs"
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs'{% if ReportType == 'NetMap' %},'tab_exploit','tab_methodology','tab_calculators','tab_learn' {% endif %}), '');
										 HideDivs(new Array('filter','review','runlog','logs'{% if ReportType == 'NetMap' %},'exploit', 'methodology','calculators','learn'{% endif %}));
										 this.className = 'selected'; 
										 ToggleDiv('logs');" >
							Logs
						</a>
				</li>
				{% if ReportType == 'NetMap' %}
				<li>
						Miscelaneous
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_exploit"
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');
										 HideDivs(new Array('filter','review','runlog','logs','exploit', 'methodology','calculators','learn'));
										 this.className = 'selected'; 
										 ToggleDiv('exploit');" >
							Exploitation
						</a>
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_methodology"
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');
										 HideDivs(new Array('filter','review','runlog','logs','exploit', 'methodology','calculators','learn'));
										 this.className = 'selected'; 
										 ToggleDiv('methodology');" >
							Methodology
						</a>
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_calculators"
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');
										 HideDivs(new Array('filter','review','runlog','logs','exploit', 'methodology','calculators','learn'));
										 this.className = 'selected'; 
										 ToggleDiv('calculators');" >
							Calculators
						</a>
				</li>
				<li>
						<a href="javascript:void(0);" id="tab_learn"
								onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');
										 HideDivs(new Array('filter','review','runlog','logs','exploit', 'methodology','calculators','learn'));
										 this.className = 'selected'; 
										 ToggleDiv('learn');" >
							Test/Learn
						</a>
				</li>
				{% endif %}
				<li class="icon">
					<a href="javascript:void(0);" class="icon" onclick="ShowDivs(new Array('filter','review','runlog','logs','exploit','methodology','calculators','learn'));SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');" target="">
						<span><img src="images/plus_gray16x16.png" title="Expand Plugins"></span>
					</a>&nbsp;
					<a href="javascript:void(0);" class="icon" onclick="HideDivs(new Array('filter','review','runlog','logs','exploit','methodology','calculators','learn'));SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');" target="">
						<span><img src="images/minus_gray16x16.png" title="Close Plugins"></span></a>
				    <a href="javascript:void(0);" style="display: none;" class="icon_unfilter" onclick="SetClassNameToElems(new Array('tab_filter','tab_review','tab_runlog','tab_logs','tab_exploit','tab_methodology','tab_calculators','tab_learn'), '');UnfilterBrotherTabs(this)" target="">
				    <span>&nbsp;<img src="images/info24x24.png" title="Show all plugins under this test item"></span>
				    </a>
				</li>
			</ul>
			""" )

			tabs_vars = {
					"ReportType": self.ReportType,
					}

			template = Template( """
			<html>
				<head>
					<title> {{ Title }}</title>
					<link rel="stylesheet" href="includes/stylesheet.css" type="text/css">
					<link rel="stylesheet" href="includes/jquery-ui-1.9m6/themes/base/jquery.ui.all.css">
				</head>
			<body {% if ReportType == 'NetMap' %} style="overflow-x:hidden;" {% endif %}>
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
								<div style="position: absolute; top: 6px; right: 6px; float: right;"> {% if ReportType != 'NetMap' %} {{ TabsStr }} {% endif %} </div>
							
							 </div>
								{% if ReportType !="NetMap" %} <div style='display:none;'> {% endif %}
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
				
				{% if ReportType == 'NetMap' %} {{ TabsStr }} {% endif %}
				<div class="iframe_padding"></div>
				<div id="filter" class="tabContent" style="display:none">
						<!-- filters -->
						<div style="display:inline;">
							<table class="counter"> 
									<tr>
										<td><div id="filtermatches_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" id="filtermatches" onclick="">
										<span> <img src="images/target.png" title="Number of plugins that matched the search"> </span>
											</a>
										</td>
					
										<td><div id="filterinfo_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" id="filterinfo" onclick="FilterResults('info', '{{ ReportType }}')">
										<span> <img src="images/info.png" title="Show only completed plugins"> </span>
											</a>
										</td>
							
										<td><div id="filterno_flag_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" id="filterno_flag" onclick="FilterResults('no_flag', '{{ ReportType }}')">
										<span> <img src="images/envelope.png" title="Show only plugins without a flag"> </span>
											</a>
										</td>
							
										<td><div id="filterunseen_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('unseen', '{{ ReportType }}')"  id="filterunseen">
										<span> <img src="images/eraser.png" title="Show only not stricken-through plugins"> </span>
											</a>
										</td>
										
										<td><div id="filterseen_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('seen', '{{ ReportType }}')"  id="filterseen">
										<span> <img src="images/pencil.png" title="Show only stricken-through plugins"> </span>
											</a>
										</td>
						
										<td><div id="filternotes_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('notes', '{{ ReportType }}')" id="filternotes" >
										<span> <img src="images/lamp_active.png" title="Show only plugins with comments"> </span>
											</a>
										</td>
							
										<td><div id="filterattention_orange_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon"  onclick="FilterResults('attention_orange', '{{ ReportType }}')" id="filterattention_orange">
										<span> <img src="images/attention_orange.png" title="Warning"> </span>
											</a>
										</td>
						
										<td><div id="filterbonus_red_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon"  onclick="FilterResults('bonus_red', '{{ ReportType }}')"  id="filterbonus_red">
										<span> <img src="images/bonus_red.png" title="Exploitable"> </span>
											</a>
										</td>
				
										<td><div id="filterstar_3_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('star_3', '{{ ReportType }}')"  id='filterstar_3'>
										<span> <img src="images/star_3.png" title="Brief look (no analysis)"> </span>
											</a>
										</td>

										<td><div id="filterstar_2_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('star_2', '{{ ReportType }}')" id="filterstar_2">
										<span> <img src="images/star_2.png" title="Initial look (analysis incomplete)"> </span>
											</a>
										</td>

										<td><div id="filtercheck_green_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon"  onclick="FilterResults('check_green', '{{ ReportType }}')" id="filtercheck_green">
										<span> 
											<img src="images/check_green.png" title="Test Passed"> </span>
											</a>
										</td>

										<td><div id="filterbug_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('bug', '{{ ReportType }}')" id="filterbug">
										<span> <img src="images/bug.png" title="Functional/Business Logic bug"> </span>
											</a>
										</td>

										<td><div id="filterflag_blue_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('flag_blue', '{{ ReportType }}')" id="filterflag_blue">
										<span> <img src="images/flag_blue.png" title="Low Severity"> </span>
											</a>
										</td>
										<td><div id="filterflag_yellow_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('flag_yellow', '{{ ReportType }}')" id="filterflag_yellow">
										<span> <img src="images/flag_yellow.png" title="Medium Severity"> </span>
											</a>
										</td>

										<td><div id="filterflag_red_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('flag_red', '{{ ReportType }}')" id="filterflag_red">
										<span> <img src="images/flag_red.png" title="High Severity"> </span>
											</a>
										</td>

										<td><div id="filterflag_violet_counter" class="counter"></div></td>
										<td>
											<a href="javascript:void(0);" class="icon" onclick="FilterResults('flag_violet', '{{ ReportType }}')" id="filterflag_violet">
												<span> <img src="images/flag_violet.png" title="Critical Severity"> </span>
											</a>
										</td>

										<td><div id="filterdelete_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="FilterResults('delete', '{{ ReportType }}')" id="filterdelete">
										<span> <img src="images/delete.png" title="Remove filter (show summary only)"> </span>
											</a>
										</td>
										<td><div id="filteroptions_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon" onclick="ToggleFilterOptions()" id="filteroptions">
										<span> <img src="images/options.png" title="Refresh Report"> </span>
											</a>
										</td>
										<td><div id="filterrefresh_counter" class="counter"></div></td>
										<td>
										<a href="javascript:void(0);" class="icon"  onclick="FilterResults('refresh', '{{ ReportType }}')" id="filterrefresh">
										<span> <img src="images/refresh.png" title="More Options"> </span>
											</a>
										</td>
									</tr>
							</table>
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
																			{{ Item["Code"]|e }} - {{ Item["Descript"]|e }} - {{ Item["Hint"]|e }} 
																		 </option>
																	{% endfor %}
																</select>
														</td>
													</tr>
												</table>
							</div>
						</div>

				</div>
				<div id="review" class="tabContent" style="display:none">
					<ul id="tabs">
						<li>
								<a href="javascript:void(0);" id="tab_review_import_export" target=""
										onclick="SetClassNameToElems(new Array('tab_review_import_export','tab_review_delete','tab_review_miscelaneous'), '');
												 HideDivs(new Array('review_import_export','review_delete', 'review_miscelaneous'));
												 this.className = 'selected'; 
												 ToggleDiv('review_import_export');" >
									Import/Export
								</a>
							</li>
							<li>
								<a href="javascript:void(0);" id="tab_review_delete" target=""
										onclick="SetClassNameToElems(new Array('tab_review_import_export','tab_review_delete','tab_review_miscelaneous'), '');
												 HideDivs(new Array('review_import_export','review_delete', 'review_miscelaneous'));
												 this.className = 'selected'; 
												 ToggleDiv('review_delete');" >
									Delete
								</a>
							</li>
							<li>
								<a href="javascript:void(0);" id="tab_review_miscelaneous" target=""
										onclick="SetClassNameToElems(new Array('tab_review_import_export','tab_review_delete','tab_review_miscelaneous'), '');
												 HideDivs(new Array('review_import_export','review_delete', 'review_miscelaneous'));
												 this.className = 'selected'; 
												 ToggleDiv('review_miscelaneous');" >
									Miscelaneous
								</a>
							</li>
							
							<li class="icon">
								<a href="javascript:void(0);" class="icon" onclick="ShowDivs(new Array('review_import_export','review_delete', 'review_miscelaneous'));SetClassNameToElems(new Array('tab_review_import_export','tab_review_delete','tab_review_miscelaneous'), '');">
									<span>
										<img src="images/plus_gray16x16.png" title="Expand Plugins">&nbsp; 
									</span>
								</a>	
								&nbsp;
								<a href="javascript:void(0);" class="icon" onclick="HideDivs(new Array('review_import_export','review_delete', 'review_miscelaneous'));SetClassNameToElems(new Array('tab_review_import_export','tab_review_delete','tab_review_miscelaneous'), '');">
									<span>
										<img src="images/minus_gray16x16.png" title="Close Plugins">&nbsp; 
									</span>
								</a>
								&nbsp;	
								<a href="javascript:void(0);" class="icon_unfilter"  style='display: none;' onclick="SetClassNameToElems(new Array('tab_review_import_export','tab_review_delete','tab_review_miscelaneous'), '');UnfilterBrotherTabs(this);">
									<span>
										<img src="images/info24x24.png" title="Show all plugins under this test item">&nbsp; 
									</span>
								</a>
							</li>
				</ul>
				&nbsp;
					<div id="review_import_export" class="tabContent" style="display:none">
								<ul class="default_list">
										<li><a href="javascript:void(0);" class="button" onclick="ImportReview();">
											<span> Import Review </span>
										</a></li>
										<li><a href="javascript:void(0);" class="button" onclick="ExportReviewAsText();">
											<span> Export Review as text </span>
										</a></li>
									</ul>
									<li><textarea rows="20" cols="100" id="import_export_box"></textarea></li>
								
					</div>
					&nbsp;
					<div id="review_delete" class="tabContent" style="display:none">
								<ul class="default_list">
									
									<li><a href="javascript:void(0);" class="button" onclick="ClearReview();">
										<span> Delete THIS Review </span>
									</a></li>
									<li><a href="javascript:void(0);" class="button" onclick="DeleteStorage();">
										<span> Delete ALL Reviews </span>
									</a></li>
								</ul>
					</div>
					&nbsp;
					<div id="review_miscelaneous" class="tabContent" style="display:none">
								<ul class="default_list">
									<li><a href="javascript:void(0);" class="button" onclick="ShowUsedMem();">
										<span> Show Used Memory (KB) </span>
									</a></li>
									<li><a href="javascript:void(0);" class="button" onclick="ShowUsedMemPercentage();">
										<span> Show Used Memory (%) </span>
									</a></li>
									<li><a href="javascript:void(0);" class="button" onclick="ShowDebugWindow();">
										<span> Show Debug Window </span>
									</a></li>
									<li><a href="javascript:void(0);" class="button" onclick="HideDebugWindow();">
										<span> Hide Debug Window </span>
									</a>
								</ul>
					</div>
				</div>
				<div id="runlog" class="tabContent" style="display:none">
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
				</div>
				<div id="logs" class="tabContent" style="display:none">
					<table class="run_log"> 
						<tr> 
							<th> General </th> 
							<th> Verified URLs </th> 
							<th> Potential URLs </th> 
						</tr>
						<tr>
							<td> 
								<ul class="default_list">
									
								<li><a href="{{ Logs.Errors.link }}" class="button" target="_blank">
									<span> 
										
										{% if Logs.Errors.nb %} 
											<font color='red'>Errors:Found, please report!</font>
										{% else  %}
											Errors: Not found
										{% endif %}
											
								    </span>
								    
								</a></li>
								<li>
								<a href="{{ Logs.Unreachables.link }}" class="button" target="_blank">
									<span> 
										
										{% if Logs.Unreachables.nb %} 
											<font color='red'>Unreachable targets: 'Yes!</font>
										{% else  %}
											Unreachable targets: No
										{% endif %}
											
								    </span>
								</a></li>
								<li>
								<a href="{{ Logs.Transaction_Log_HTML.link }}" class="button" target="_blank">
									<span> 	Transaction Log (HTML) </span>
								</a></li>
								<li>
								<a href="{{ Logs.All_Downloaded_Files.link }}" class="button" target="_blank">
									<span> 	All Downloaded Files - To be implemented </span>
								</a></li>
								<li>
								<a href="{{ Logs.All_Transactions.link }}" class="button" target="_blank">
									<span> All Transactions </span>
								</a></li>
								<li>
								<a href="{{ Logs.All_Requests.link }}" class="button" target="_blank">
									<span> 	All Requests </span>
								</a></li>
								<li>
								<a href="{{ Logs.All_Response_Headers.link }}" class="button" target="_blank">
									<span> 	All Response Headers </span>
								</a></li>
								<li>
								<a href="{{ Logs.All_Response_Bodies.link }}" class="button" target="_blank">
									<span> 	All Response Bodies </span>
								</a></li>
								</ul>

							 </td> 
							<td> 
								<ul class="default_list">
									<li>
									<a href="{{ Urls.All_URLs_link }}" class="button" target="_blank">
										<span> 	All URLs </span>
									</a></li>
									<li>
									<a href="{{ Urls.File_URLs_link }}" class="button" target="_blank">
										<span> File URLs </span>
									</a></li>
									<li>
									<a href="{{ Urls.Fuzzable_URLs_link }}" class="button" target="_blank">
										<span> Fuzzable URLs </span>
									</a></li>
									<li>
									<a href="{{ Urls.Image_URLs_link }}" class="button" target="_blank">
										<span> 	Image URLs </span>
									</a></li>
									<li>
									<a href="{{ Urls.Error_URLs_link }}" class="button" target="_blank">
										<span> 	Error URLs </span>
									</a></li>
									<li>
									<a href="{{ Urls.External_URLs_link }}" class="button" target="_blank">
										<span> 	External URLs </span>
									</a></li>
									</ul>

							 </td> 
									<td> 
										<ul class="default_list">
											<li>
											<a href="{{ Urls_Potential.All_URLs_link }}" class="button" target="_blank">
												<span> 	All URLs </span>
											</a></li>
											<li>
											<a href="{{ Urls_Potential.File_URLs_link }}" class="button" target="_blank">
												<span> File URLs </span>
											</a></li>
											<li>
											<a href="{{ Urls_Potential.Fuzzable_URLs_link }}" class="button" target="_blank">
												<span> Fuzzable URLs </span>
											</a></li>
											<li>
											<a href="{{ Urls_Potential.Image_URLs_link }}" class="button" target="_blank">
												<span> 	Image URLs </span>
											</a></li>
											<li>
											<a href="{{ Urls_Potential.Error_URLs_link }}" class="button" target="_blank">
												<span> 	Error URLs </span>
											</a></li>
											<li>
											<a href="{{ Urls_Potential.External_URLs_link }}" class="button" target="_blank">
												<span> 	External URLs </span>
											</a>
											</li>
										</ul>
									 </td> 
						</tr>
					</table>
				</div>
			   {% if ReportType == 'NetMap' %}
				<div id="exploit" class="tabContent" style="display:none">
					<ul class="default_list">
						<li>
						<a href="http://hackvertor.co.uk/public" class="button" target="_blank">
							<span> Hackvertor </span>
						</a></li>
						<li>
						<a href="http://hackarmoury.com/" class="button" target="_blank">
							<span> Hackarmoury </span>
						</a></li>
						<li>
						<a href="http://www.exploit-db.com/" class="button" target="_blank">
							<span> ExploitDB </span>
						</a></li>
						<li>
						<a href="http://www.exploitsearch.net" class="button" target="_blank">
							<span> ExploitSearch </span>
						</a></li>
						<li>
						<a href="http://www.hakipedia.com/index.php/Hakipedia" class="button" target="_blank">
							<span> hackipedia </span>
						</a></li>
					</ul>
				</div>	
				<div id="methodology" class="tabContent" style="display:none">
					<ul class="default_list">
					<li>
						<a href="https://www.owasp.org/index.php/OWASP_Testing_Guide_v3_Table_of_Contents" class="button" target="_blank">
							<span> OWASP </span>
						</a></li>
					<li>
						<a href="http://www.pentest-standard.org/index.php/Main_Page" class="button" target="_blank">
							<span> Pentest Standard </span>
						</a></li>
					<li>
						<a href="http://www.isecom.org/osstmm/" class="button" target="_blank">
							<span> OSSTMM </span>
						</a></li>
					</ul>
				</div>
			
				<div id="calculators" class="tabContent" style="display:none">
					<ul class="default_list">
						<li><a href="http://nvd.nist.gov/cvss.cfm?adv&calculator&version=2" class="button" target="_blank">
							<span> CVSS Advanced </span>
						</a></li><li>
						<a href="http://nvd.nist.gov/cvss.cfm?calculator&version=2" class="button" target="_blank">
							<span> CVSS Normal </span>
						</a></li>
					</ul>
				</div>		
				<div id="learn" class="tabContent" style="display:none">
					<ul class="default_list">
						<li><a href="http://blog.taddong.com/2011/10/hacking-vulnerable-web-applications.html" class="button" target="_blank">
							<span> Taddong </span>
						</a></li>
						<li>
							<a href="http://securitythoughts.wordpress.com/2010/03/22/vulnerable-web-applications-for-learning/" class="button" target="_blank">
							<span> Securitythoughts </span>
						</a></li>
						<li>
						<a href="http://danielmiessler.com/projects/webappsec_testing_resources/" class="button" target="_blank">
							<span> Danielmiessler </span>
						</a></li>
					</ul>
				</div>	
			{% endif %}		
					<script type="text/javascript" src="includes/jquery-1.6.4.js"></script>\n
					<script type="text/javascript" src="includes/owtf_general.js"></script>\n
					<script type="text/javascript" src="includes/owtf_review.js"></script>\n
					<script type="text/javascript" src="includes/owtf_filter.js"></script>\n
					<script type="text/javascript" src="includes/owtf_reporting.js"></script>\n
					<script type="text/javascript" src="includes/jsonStringify.js"></script>\n
					<script type="text/javascript" src="includes/ckeditor/ckeditor.js"></script>
					<script type="text/javascript" src="includes/ckeditor/adapters/jquery.js"></script>
					<script type="text/javascript" src="includes/owtf_localStorage.js"></script>
			""" )

			vars = {
						"Title" : Options['Title'],
						"ReportType" : Options['ReportType'],
						"TabsStr" : Tabs_template.render( tabs_vars ),
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
