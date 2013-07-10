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
from collections import defaultdict
from framework.lib.general import *
from framework.report import header, summary
from framework.report.html import renderer
from framework.report.html.filter import sanitiser
from psycopg2.extras import logging
import os
import re
import cgi
import sys
import time

PLUGIN_DELIM = '__' # Characters like ; | . or / trip CKEditor as separators
REPORT_PREFIX = '__rep__'

class Reporter:
	def __init__(self, CoreObj):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False
		self.Render = renderer.HTMLRenderer(self.Core)
		self.Header = header.Header(self.Core)
		self.Summary = summary.Summary(self.Core)
		self.Sanitiser = sanitiser.HTMLSanitiser()
		self.PluginDivIds = {}
		self.CounterList = []

        def DrawImageFromConfigPair(self, ConfigList):
                FileName, ToolTip = self.Core.Config.GetAsList(ConfigList)
                return self.Render.DrawImage(FileName, { 'title' : ToolTip })

	def GetPluginDelim(self):
		return PLUGIN_DELIM

        def GetPluginDivId(self, Plugin):
                # "Compression" attempt while keeping uniqueness:
                # First letter from plugin type is enough to make plugin div ids unique and predictable
                #return MultipleReplace(Code, { 'OWASP' : 'O', 'OWTF' : 'F', '-' : '', '0' : '' })+PluginType[0]
                return self.GetPluginDelim().join( [ Plugin['Group'], Plugin['Type'], Plugin['Code'] ] ) # Need this info for fast filtering in JS

        def DrawCommand(self, Command):
                #cgi.escape(MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict()))
                return cgi.escape(Command)#.replace(';', '<br />') -> Sometimes ";" encountered in UA, cannot do this and it is not as helpful anyway

        def DrawCommandTable(self, Command):
                Table = self.Render.CreateTable({'class' : 'run_log'})
                Table.CreateRow( [ 'Analysis Command' ], True)
                Table.CreateRow( [ self.DrawCommand(Command) ] )
                return Table.Render()

	def DrawHelpLink(self, Anchor):
		return self.Render.DrawLink(self.DrawImageFromConfigPair( [ 'FIXED_ICON_REVIEW_SIZE_HELP', 'NAV_TOOLTIP_REVIEW_SIZE_HELP' ] ), 'includes/help/help.html#'+Anchor, { 'target' : '_blank' } )

	def GetIconLinks(self, IconList, Options):
		List = []
		for I in IconList:
			if I['Icon'] == I['Icon'].upper(): # Icon in capitals = config setting
				for Item in [ 'Icon', 'ToolTip' ]:
					I[Item] = self.Core.Config.Get(I[Item]) # Override settings with config values
			Image = self.Render.DrawImage(I['Icon'], { 'title' : I['ToolTip'] })
			Attribs = { 'class' : 'icon' }
			if 'Attribs' in I:
				Attribs = I['Attribs'].copy()
			if 'id' in Attribs:
				pass # id already passed, ignore below
			elif 'CounterName' in I:
				Attribs['id'] = Options['IdPrefix'] + I['CounterName'] # Give each counter a unique id
			elif 'IdPrefix' in Options: # Each link must have a unique id
				#Attribs['id'] = Options['IdPrefix'] + I['Function'].split('(')[0] # Give each link a unique id
				Attribs['id'] = Options['IdPrefix'] + I['Icon']
                        LinkImage = self.Render.DrawButtonJSLink(Image, I['Function'], Attribs)
			PrefixStr = ''
			if 'Counters' in Options and 'IdPrefix' in Options: 
				#Counters are drawn in a table, list is a row of HTML table cells with counters:
				CounterName = I['Icon']
				if 'CounterName' in I:
					CounterName = I['CounterName']
				CounterId = Options['IdPrefix']+CounterName+'_counter'
                                self.CounterList.append(CounterId)
				PrefixStr = '<td>' + self.Render.DrawDiv('', { 'id' : CounterId, 'class' : 'counter' }) + '</td>'
			List.append(PrefixStr + '<td>' + LinkImage + '</td>')
		return List

        def DrawReviewIconLinks(self, IconList, Options): # Options = {}
		Table = self.Render.CreateTable({'class' : 'counter'})
		Table.CreateCustomRow( '<tr>' + ''.join(self.GetIconLinks(IconList, Options)) + '</tr>'  )
		DivStyle = 'display:inline;'
		if not 'Counters' in Options:
			DivStyle += 'float:right;'
		return self.Render.DrawDiv(Table.Render() + self.DrawFilterOptions(), { 'style' : DivStyle })

	def GetSelectListFromList(self, List):
		NewList = []
		for Item in List:
			NewList.append( [ Item, Item ] ) 
		return NewList

	def GetSelectListFromDict(self, Dict, ValueField, ConcatDescripFieldList, ConcatStr = '-'):
		List = []
		for Item in Dict:
			FieldList = []
			for Field in ConcatDescripFieldList:
				#if not Field.strip(): continue
				#print "Field=" + str(Field) + str(ConcatDescripFieldList)
				FieldList.append(Item[Field])
			List.append( [ Item[ValueField], ConcatStr.join(FieldList) ] )
		return List

	def DrawFilterOptions(self):
		TableG = self.Render.CreateTable( { 'class' : 'transaction_log' } )
		TableG.CreateRow( [ 'Plugin Groups', 'Web Plugin Types', 'Aux Plugin Types' ], True)
		#multiple, size, autocomplete, disabled, name, id
		TableG.CreateRow( [ 
self.Render.DrawSelect(self.GetSelectListFromList(self.Core.Config.Plugin.GetAllGroups()), [], { 'multiple' : 'multiple', 'id' : 'SelectPluginGroup', 'onchange' : 'SetSelectFilterOptions(this)' })
, self.Render.DrawSelect(self.GetSelectListFromList(self.Core.Config.Plugin.GetTypesForGroup('web')), [], { 'multiple' : 'multiple', 'id' : 'SelectPluginTypesWeb', 'size' : '6', 'onchange' : 'SetSelectFilterOptions(this)' })
, self.Render.DrawSelect(self.GetSelectListFromList(self.Core.Config.Plugin.GetTypesForGroup('aux')), [], { 'multiple' : 'multiple', 'id' : 'SelectPluginTypesAux', 'size' : '6', 'onchange' : 'SetSelectFilterOptions(this)' })
] )
		TableD = self.Render.CreateTable( { 'class' : 'transaction_log' } )
		TableD.CreateRow( [ 'Web Test Groups' ], True)
		TableD.CreateRow( [ 
self.Render.DrawSelect(self.GetSelectListFromDict(self.Core.Config.Plugin.GetWebTestGroups(), 'Code', [ 'Code', 'Descrip', 'Hint' ], ' - ' ), [], { 'multiple' : 'multiple', 'id' : 'SelectWebTestGroups', 'size' : '10', 'onchange' : 'SetSelectFilterOptions(this)' })
] )
		return self.Render.DrawDiv( '<h4>Filter Options</h4><p>Tip: Hold the Ctrl key while selecting or unselecting for multiple choices.<br />NOTE: Clicking on any filter will apply these options from now on. Options will survive a screen refresh</p>' + TableG.Render() + TableD.Render(), { 'id' : 'advanced_filter_options', 'style' : 'display: none;' })

        def DrawCounters(self, ReportType, IdPrefix = 'filter'):
		ReportTypeStr = "'" + ReportType + "'"
		FixedStartIcons = [
{ 'Icon' : 'FIXED_ICON_MATCHES', 'ToolTip' : 'FILTER_TOOLTIP_MATCHES', 'Function' : "", 'CounterName' : 'matches' },
{ 'Icon' : 'FIXED_ICON_INFO', 'ToolTip' : 'FILTER_TOOLTIP_INFO', 'Function' : "FilterResults('info', "+ReportTypeStr+")", 'CounterName' : 'info' },
{ 'Icon' : 'FIXED_ICON_NOFLAG', 'ToolTip' : 'FILTER_TOOLTIP_NOFLAG', 'Function' : "FilterResults('no_flag', "+ReportTypeStr+")", 'CounterName' : 'no_flag' },
{ 'Icon' : 'FIXED_ICON_UNSTRIKETHROUGH', 'ToolTip' : 'FILTER_TOOLTIP_UNSTRIKETHROUGH', 'Function' : "FilterResults('unseen', "+ReportTypeStr+")", 'CounterName' : 'unseen' },
{ 'Icon' : 'FIXED_ICON_STRICKETHROUGH', 'ToolTip' : 'FILTER_TOOLTIP_STRIKETHROUGH', 'Function' : "FilterResults('seen', "+ReportTypeStr+")", 'CounterName' : 'seen' },
{ 'Icon' : 'FIXED_ICON_NOTES', 'ToolTip' : 'FILTER_TOOLTIP_NOTES', 'Function' : "FilterResults('notes', "+ReportTypeStr+")", 'CounterName' : 'notes' }
]
		DynamicIcons = self.GetChosenReviewIconList('', 'FilterResults', ReportTypeStr) 
		
		Counters = FixedStartIcons + DynamicIcons

		Counters += [
{ 'Icon' : 'FIXED_ICON_REMOVE', 'ToolTip' : 'FILTER_TOOLTIP_REMOVE_FILTER', 'Function' : "FilterResults('delete', "+ReportTypeStr+")" },
{ 'Icon' : 'FIXED_ICON_OPTIONS', 'ToolTip' : 'FILTER_TOOLTIP_OPTIONS', 'Function' : "ToggleFilterOptions()" },
{ 'Icon' : 'FIXED_ICON_REFRESH', 'ToolTip' : 'FILTER_TOOLTIP_REFRESH', 'Function' : "FilterResults('refresh', "+ReportTypeStr+")" }
]
		return self.DrawReviewIconLinks(Counters, { 'IdPrefix' : IdPrefix, 'Counters' : True })

	def GetChosenReviewIconList(self, DivId, Function, ReportTypeStr = ''): # This list is dynamic: depends on what the user configured
		List = []
                Setting = 'CHOSEN_ICONS_FOR_REVIEW'
		for IconInfo in self.Core.Config.Get(Setting).split(','):
                        IconInfo = IconInfo.split('@') # Convert from config file
                        if len(IconInfo) != 2:
                                self.Core.Error.Add("USER ERROR: Error in conf. file setting: CHOSEN_ICONS_FOR_REVIEW -> icon@title ("+str(IconInfo)+")", 'user')
                                break # Abort loop + end processing
                        Icon, Title = IconInfo
			FunctionStr = "FilterResults('"+Icon+"', "+ReportTypeStr+")" 
			if 'Rate' == Function:
				FunctionStr = "Rate('"+DivId+"', '"+Icon+"', this)"
			List.append( { 'Icon' : Icon, 'ToolTip' : Title, 'Function' : FunctionStr } )
                if len(List) == 0: # Must select at least 1 flag
                        self.Core.Error.Add("USER ERROR: Error in configuration file -> no items selected for setting: "+Setting, 'user')
                        return []
		return List

	def GetReviewIconList(self, DivId):
		FixedStartIcons = [
{ 'Icon' : 'FIXED_ICON_NOTES', 'ToolTip' : 'REVIEW_TOOLTIP_NOTES', 'Function' : "ToggleNotesBox('"+DivId+"')" },
{ 'Icon' : 'FIXED_ICON_STRICKETHROUGH', 'ToolTip' : 'REVIEW_TOOLTIP_STRIKETHROUGH', 'Function' : "MarkAsSeen('"+DivId+"')", 'Attribs' : { 'id' : 'l'+DivId, 'class' : 'icon' } }
]
		DynamicIcons = self.GetChosenReviewIconList(DivId, 'Rate') 
		
		FixedEndIcons = [
{ 'Icon' : 'FIXED_ICON_REMOVE', 'ToolTip' : 'REVIEW_TOOLTIP_REMOVE', 'Function' : "Rate('"+DivId+"', 'delete', this)" },
{ 'Icon' : 'FIXED_ICON_CLOSE_PLUGIN', 'ToolTip' : 'REVIEW_TOOLTIP_CLOSE_PLUGIN', 'Function' : "HidePlugin('"+DivId+"')" }
]
		return FixedStartIcons + DynamicIcons + FixedEndIcons

        def DrawReviewButtons(self, DivId):
		return self.DrawReviewIconLinks(self.GetReviewIconList(DivId), { 'IdPrefix' : DivId } )

        def DrawTransacLinksStr(self, PathList, ToFile = True):
                URL, TransacPath, ReqPath, ResHeadersPath, ResBodyPath = PathList
                LinksStr = self.Render.DrawButtonLink('Site', URL)+" "
                LinksStr += " ".join(self.Render.DrawLinkPairs([['F', TransacPath ], ['R', ReqPath], ['H', ResHeadersPath], ['B', ResBodyPath]], 'DrawButtonLink', {}, ToFile))
                return LinksStr

        def DrawTransacLinksForID(self, ID, ForPlugin = False):
                PathList = self.Core.DB.Transaction.GetTransactionPathsForID(ID) # Returns the URL and Transaction Paths for a given Transaction ID
		CleanPathList = [PathList[0]] # Leave URL unmodified
		if ForPlugin:
			for Path in PathList[1:]:#Skip URL, process rest of items in list = File paths
				CleanPathList.append('../../../'+Path)
		else:
			CleanPathList = PathList
                return self.DrawTransacLinksStr(CleanPathList)

        def SavePluginReport(self, HTMLtext, Plugin):
                save_dir = self.Core.PluginHandler.GetPluginOutputDir(Plugin)
                if HTMLtext == None:
                        HTMLtext = cprint("PLUGIN BUG!!: on: "+PluginType.strip()+"/"+PluginFile.strip()+" no content returned")
                DivId = self.GetPluginDivId(Plugin)
                PluginReportPath = save_dir + "report.html"
                self.Core.CreateMissingDirs(save_dir)
                with open(PluginReportPath, 'w') as file: # 'w' is important to overwrite the partial report, necesary for scanners
                        Table = self.Render.CreateTable({ 'class' : 'report_intro' })
                        Table.CreateRow(['Plugin', 'Start', 'End', 'Runtime', 'Output Files'], True)
			Plugin['RunTime'] = self.Core.Timer.GetElapsedTimeAsStr('Plugin')
			Plugin['End'] = self.Core.Timer.GetEndDateTimeAsStr('Plugin')
                        Table.CreateRow([ Plugin['Type']+'/'+Plugin['File'], Plugin['Start'], Plugin['End'], Plugin['RunTime'], self.Core.Reporter.Render.DrawButtonLink('Browse', self.Core.GetPartialPath(save_dir)) ])
                        PluginHeader = '<h4 id="h'+DivId+'"><u>'+Plugin['Title']+'</u> - <i>'+Plugin['Type'].replace('_', ' ').upper()+'</i>'
                        PluginHeader += "&nbsp;" * 2 +self.DrawReviewButtons(DivId)+'</h4>'+Table.Render()
                        # Generate unique id every time to detect if plugin report changed to highlight modified stuff without losing review data (i.e. same plugin id):
                        PluginHeader += "<div id='token_"+DivId+"' style='display: none;'>"+self.Core.DB.GetNextHTMLID()+"</div>"
                        NotesBox = self.Render.CreateTable({ 'class' : 'transaction_log' })
                        NotesBox.CreateRow(['Notes'], True)
                        # NOTE: autocomplete must be off because otherwise you see the text but is not saved in the review at all, which is counter-intuitive
			NotesBox.CreateRow( [ '<div id="note_preview_'+DivId+'"></div><div style="float: right;"><a href="javascript:ToggleNotesBox(\'' + DivId + '\')">Edit</a></div><div id="notes_'+DivId+'" style="display: none;"><textarea id="note_text_'+DivId+'" autocomplete="off" rows=15 cols=150></textarea> </div>' ] )
                       # NotesBox.CreateRow(['<textarea id="'+TextAreaId+'" autocomplete="off" onChange="SaveComments(\''+DivId+'\')" rows=15 cols=150></textarea><script type="text/javascript">CKEDITOR.replace( "'+TextAreaId+'" );</script>'])
                       # Better with auto-save: NotesBox.CreateCustomRow('<tr><td align="right">'+self.Render.DrawButtonJSLink('<img src="images/floppy.png" />', "SaveComments('"+DivId+"')", { 'class' : 'icon' })+'</td></tr>')
                        PluginHeader += "<div>"+NotesBox.Render()+"</div><hr />"
                        #PluginHeader += "<div id='notes_"+DivId+"' style='display: none;'>"+NotesBox.Render()+"</div><hr />"
                        file.write("\n"+PluginHeader+HTMLtext+"\n")
            	#log = logging.getLogger('register') 
            	#log.info(str(os.getpid())+','+str(Plugin['RunTime'])+','+str(Plugin['End'])+','+str(Plugin['Start']))       
		#print "Plugin="+str(Plugin)
		self.Core.DB.PluginRegister.Add(Plugin, PluginReportPath, self.Core.Config.GetTarget())
                #self.RegisterPartialReport(PluginReportPath) # Partial report saved ok, register partial report in register file for grouping later
                self.ReportFinish() # Provide a full partial report at the end of each plugin

	def DrawHTTPTransactionTable(self, TransactionList, NumLinesReq = 15, NumLinesRes = 15): # Draws a table of HTTP Transactions
		Table = self.Render.CreateTable({'class' : 'transactions'})
		Table.CreateCustomRow('<tr><th colspan="2" align="center">'+'HTTP Transactions'+'</th></tr>')
		Table.CreateRow([ 'Request', 'Response' ], True)
		for Transaction in TransactionList:
			Table.CreateRow([ Transaction.GetHTMLLinkWithTime("See Transaction "+Transaction.ID)+" "+self.DrawTransacLinksForID(Transaction.ID)+'<br /><pre>'+cgi.escape(TruncLines(Transaction.GetRawRequest(), NumLinesReq))+'</pre>', '<pre>'+cgi.escape(TruncLines(Transaction.GetRawResponse(), NumLinesRes))+'</pre>' ])
		return Table.Render()

	def GetTransactionLink(self, TransacPath):
		return "/".join(TransacPath.split("/")[-5:])

        def GetIconInfoAsStr(self, InfoList):
                FileName, Title = self.Core.Config.GetAsList(InfoList)
                return FileName+'@'+Title

        def GetIconInfoPairsAsStrList(self, IconInfoPairs):
                InfoList = []
                for IconInfoList in IconInfoPairs:
                        InfoList.append(self.GetIconInfoAsStr(IconInfoList))
                return InfoList

        def ReportStart(self):
		self.CounterList = []
		ReportType = self.Core.Config.Get('REPORT_TYPE')
		self.Header.Save('HTML_DETAILED_REPORT_PATH', { 'ReportType' : ReportType, 'Title' :  ReportType+" Report" } )

	def GetRegisteredWebPlugins(self, ReportType): # Web Plugins go in OWASP Testing Guide order
		TestGroups = []
		for TestGroup in self.Core.Config.Plugin.GetWebTestGroups(): #Follow defined web test group order, NOT execution order
			RegisteredPlugins = self.Core.DB.PluginRegister.Search( { 'Code' : TestGroup['Code'], 'Target' : self.Core.Config.GetTarget() } )
			if not RegisteredPlugins:
				continue # The plugin has not been registered yet
			RegisteredPluginList = []
			for Match in RegisteredPlugins:
				Match['Label'] = Match['Type'] # For url plugins the Label is a display of the plugin type (passive, semi_passive, etc)
				RegisteredPluginList.append(Match)
			TestGroups.append( { 
'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'" class="testgroup">'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
, 'RegisteredPlugins' : RegisteredPluginList } )
			#'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'"><br />'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
		return TestGroups
        
	def GetRegisteredNetPlugins(self, ReportType): # netPlugins go in OWASP Testing Guide order
		TestGroups = []
		for TestGroup in self.Core.Config.Plugin.GetNetTestGroups(): #Follow defined web test group order, NOT execution order
			RegisteredPlugins = self.Core.DB.PluginRegister.Search( { 'Code' : TestGroup['Code'], 'Target' : self.Core.Config.GetTarget() } )
			if not RegisteredPlugins:
				continue # The plugin has not been registered yet
			RegisteredPluginList = []
			for Match in RegisteredPlugins:
				Match['Label'] = Match['Type'] # For url plugins the Label is a display of the plugin type (passive, semi_passive, etc)
				RegisteredPluginList.append(Match)
			TestGroups.append( { 
'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'" class="testgroup">'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
, 'RegisteredPlugins' : RegisteredPluginList } )
			#'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'"><br />'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
		return TestGroups



	def GetRegisteredAuxPlugins(self, ReportType): # Web Plugins go in OWASP Testing Guide order
		TestGroups = []
		for PluginType in self.Core.Config.Plugin.GetTypesForGroup('aux'): # Report aux plugins in alphabetical order
			RegisteredPlugins = self.Core.DB.PluginRegister.Search( { 'Type' : PluginType, 'Target' : 'aux' } ) # Aux plugins have an aux target
			if not RegisteredPlugins:
				continue # The plugin has not been registered yet
			RegisteredPluginList = []
			for Match in RegisteredPlugins:
				Match['Label'] = Match['Args'] # For aux plugins the Label is a display of the arguments passed
				RegisteredPluginList.append(Match)
			TestGroups.append( { 
'TestGroupHeaderStr' : '<div id="'+PluginType.lower()+'"><br />'+self.Render.DrawButtonLink(PluginType.upper(), '#', { 'class' : 'report_index' })+"&nbsp;" # No hint ..
, 'RegisteredPlugins' : RegisteredPluginList } )
		return TestGroups

	def GetTestGroups(self, ReportType):
		
		if ReportType == 'URL':
			return self.GetRegisteredWebPlugins(ReportType)
		elif ReportType == 'AUX':
			return self.GetRegisteredAuxPlugins(ReportType)
		elif ReportType == 'NET':
			return self.GetRegisteredNetPlugins(ReportType)
		

	def DrawReportSkeleton(self): # Create Div + Tab structure for Review + Report ease of navigation
		Tabs = self.Render.CreateTabs()
		for Section in [ ['stats', 'Statistics'], ['passed', 'Passed Tests'], ['findings', 'Findings'], ['unrated', 'Not Rated'] ]:
			Id, Label = Section
			Tabs.AddDiv(REPORT_PREFIX + Id, Label, '')
		Tabs.CreateTabs()
		Tabs.CreateTabButtons()
		return """
<div id="generated_report" class="generated_report" style="display:none;">
<div id='""" + REPORT_PREFIX + """intro'></div>""" + Tabs.Render() + """</div>
<div id="review_content" class="review_content">
"""

        def ReportFinish(self): # Group all partial reports (whether done before or now) into the final report
		Target = self.Core.Config.GetTarget()
		if not self.Core.DB.PluginRegister.NumPluginsForTarget(Target) > 0:
			cprint("No plugins completed for target, cannot generate report")
			return None # Must abort here, before report is generated
                self.ReportStart() # Wipe report
                with open(self.Core.Config.Get('HTML_DETAILED_REPORT_PATH'), 'a') as file:
		        file.write('<div id="GlobalReportButtonsTop" style="display:none;"></div>' + self.DrawReportSkeleton()) # Start OWASP Testing Guide Item List
			AllPluginsTabIdList = []
			AllPluginsDivIdList = []
			AllCodes = []
			for TestGroup in self.GetTestGroups(self.Core.Config.Get('REPORT_TYPE')):
		                HeaderStr = TestGroup['TestGroupHeaderStr']
				Tabs = self.Render.CreateTabs()
				
				for Match in  TestGroup['RegisteredPlugins']:
					if Match['Code'] not in AllCodes:
						AllCodes.append(Match['Code'])
					#PluginType = Match['Type']
					#DivId = self.GetPluginDivId(Match['Code'], PluginType)
					DivId = self.GetPluginDivId(Match)
					Tabs.AddDiv(DivId, Match['Label'], open(Match['Path']).read())
					AllPluginsTabIdList.append(Tabs.GetTabIdForDiv(DivId))
					AllPluginsDivIdList.append(DivId)
				if Tabs.GetNumDivs() > 0:
					Tabs.CreateCustomTab('Results:') # First create custom tab, without javascript
					Tabs.CreateTabs() # Create the hide/show deal tabs
					Tabs.CreateTabButtons() # Add handy tab navigation buttons to the right
					HeaderStr += "&nbsp;" * 1 + ("&nbsp;" * 1).join(self.Render.DrawLinkPairs( [ [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_EXPAND_REPORT', 'NAV_TOOLTIP_EXPAND_REPORT' ]), "ClickLinkById('expand_report')" ], [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_CLOSE_REPORT', 'NAV_TOOLTIP_CLOSE_REPORT' ]), "ClickLinkById('collapse_report')" ] ], 'DrawButtonJSLink', { 'class' : 'icon' }))
				#HeaderStr += "<br />"
       				file.write(HeaderStr+Tabs.Render()+"</div>") # Save plugin reports in OWASP Guide order => 1 write per item = less memory-intensive
			if len(AllPluginsTabIdList) == 0:
				cprint("ERROR: No plugins found, cannot write report")
				return None # No plugins found (should not happe)
			UnhighlightReportPluginTabsJS = "SetClassNameToElems("+self.Render.DrawJSArrayFromList(AllPluginsTabIdList)+", '')"
			PluginDivs = self.Render.DrawJSArrayFromList(AllPluginsDivIdList)
			HideReportPluginDivsJS = UnhighlightReportPluginTabsJS+"; HideDivs("+PluginDivs+")"
			ShowReportPluginDivsJS = UnhighlightReportPluginTabsJS+"; ShowDivs("+PluginDivs+")"
			file.write("""</div>
<br />
<div id='GlobalReportButtonsBottom' style='display:none;'>"""+self.Render.DrawButtonJSLink('+', ShowReportPluginDivsJS, { 'id' : 'expand_report' })+"&nbsp;"+self.Render.DrawButtonJSLink('-', HideReportPluginDivsJS, { 'id' : 'collapse_report' })+"""</div>
<script>
var AllPlugins = """ + PluginDivs + """
var AllCodes = """ + self.Render.DrawJSArrayFromList(AllCodes) + """
var Offset = '""" + self.Core.Config.Get('REVIEW_OFFSET') + """'
""" + self.DrawJSCounterList() + """
var DetailedReport = true
var PluginDelim = '""" + self.GetPluginDelim() + """'
var ReportMode = false
var REPORT_PREFIX = '""" + REPORT_PREFIX + """'
</script>
</body></html>""") # Closing HTML Report
                        log = logging.getLogger('general')
			log.info("Report written to: "+self.Core.Config.Get('HTML_DETAILED_REPORT_PATH'))
			self.Core.DB.ReportRegister.Add(self.Core.Config.GetAsList( [ 'REVIEW_OFFSET', 'SUMMARY_HOST_IP', 'SUMMARY_PORT_NUMBER', 'HTML_DETAILED_REPORT_PATH', 'REPORT_TYPE' ] )) # Register report
			self.Summary.ReportFinish() # Build summary report

	def DrawJSCounterList(self):
		return """var AllCounters = """+self.Render.DrawJSArrayFromList(self.CounterList)

        def ReportWrite(self, html, text):
                cprint(text) # Text displayed on console only, html saved in report
                with open(self.Core.Config.Get('HTML_DETAILED_REPORT_PATH'), 'a') as file:
                        file.write(html) # Closing HTML Report
