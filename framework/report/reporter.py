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
from framework.lib.general import *
from framework.report.html import renderer
from framework.report import header, summary
from collections import defaultdict

class Reporter:
	def __init__(self, CoreObj):
		self.Core = CoreObj # Keep Reference to Core Object
		self.Init = False
		self.Render = renderer.HTMLRenderer(self.Core)
		self.Header = header.Header(self.Core)
		self.Summary = summary.Summary(self.Core)
		self.PluginDivIds = {}
		self.CounterList = []

        def DrawCommand(self, Command):
                #cgi.escape(MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict()))
                return cgi.escape(Command)#.replace(';', '<br />') -> Sometimes ";" encountered in UA, cannot do this and it is not as helpful anyway

        def DrawCommandTable(self, Command):
                Table = self.Render.CreateTable({'class' : 'run_log'})
                Table.CreateRow( [ 'Analysis Command' ], True)
                Table.CreateRow( [ self.DrawCommand(Command) ] )
                return Table.Render()

        def GetIconFunction(self, Icon, IconToFunction, DivId = ''):
                Function = Icon
                if Icon in IconToFunction:
                        Function = IconToFunction[Icon]
                FunctionStr = "FilterResults('"+Function+"')"
                if len(DivId) > 0:
                        FunctionStr = "Rate('"+DivId+"', '"+Function+"')"
                return [ Function, FunctionStr ]

        def DrawReviewIconLinks(self, IconList, IconToFunction, DivId = '', IdPrefix = None, Counters = False):
                Setting = 'CHOSEN_ICONS_FOR_REVIEW'
                DrawList = []
                for IconInfo in IconList:
                        IconInfo = IconInfo.split('@') # Convert from config file
                        if len(IconInfo) != 2:
                                self.Core.Error.Add("USER ERROR: Error in conf. file setting: CHOSEN_ICONS_FOR_REVIEW -> icon@title ("+str(IconInfo)+")", 'user')
                                break # Abort loop + end processing
                        Icon, Title = IconInfo
                        Function, FunctionStr = self.GetIconFunction(Icon, IconToFunction, DivId)
                        #DrawList.append( [ self.Render.DrawImage(Icon, 'title' : Title }), FunctionStr ] )
                        Image = self.Render.DrawImage(Icon, { 'title' : Title })
                        Attribs = { 'class' : 'icon' }
                        if IdPrefix != None: # Each link must have a unique id
                                Attribs['id'] = IdPrefix+Function # Give each link a unique id
                        LinkImage = self.Render.DrawButtonJSLink(Image, FunctionStr, Attribs)
                        if Counters and IdPrefix != None:
                                CounterId = IdPrefix+Function+'_counter'
                                self.CounterList.append(CounterId)
                                DrawList.append('<td><div id="'+CounterId+'" class="counter">0</div></td><td>'+LinkImage+'</td>')
                                continue # Counters are drawn in a table, list is a row of HTML table cells instead of plain links like below = must skip below
                        DrawList.append( LinkImage )
                if len(DrawList) == 0: # Must select at least 1 flag
                        self.Core.Error.Add("USER ERROR: Error in configuration file -> no items selected for setting: "+Setting, 'user')
                        return ''
                #return "&nbsp;".join(self.Render.DrawLinkPairs(DrawList, 'DrawButtonJSLink', { 'class' : 'icon' }))
                if Counters:
                        Table = self.Render.CreateTable({'class' : 'counter'})
                        Table.CreateCustomRow( '<tr>'+''.join(DrawList)+'</tr>'  )
                        return Table.Render()
                return "&nbsp;".join(DrawList)

        def DrawCounters(self, Filter = False, IdPrefix = 'filter'):
                CounterList = self.GetIconInfoPairsAsStrList([
[ 'FIXED_ICON_INFO', 'FILTER_TOOLTIP_INFO' ]
, [ 'FIXED_ICON_NOFLAG', 'FILTER_TOOLTIP_NOFLAG' ]
, [ 'FIXED_ICON_UNSTRIKETHROUGH', 'FILTER_TOOLTIP_UNSTRIKETHROUGH' ]
, [ 'FIXED_ICON_STRICKETHROUGH', 'FILTER_TOOLTIP_STRIKETHROUGH' ]
, [ 'FIXED_ICON_NOTES', 'FILTER_TOOLTIP_NOTES' ]
]) # End of first fixed filter icons
                for IconInfo in self.Core.Config.Get('CHOSEN_ICONS_FOR_REVIEW').split(','): # User-configurable icons
                        CounterList.append( IconInfo )
		if Filter:
	                CounterList += self.GetIconInfoPairsAsStrList([
[ 'FIXED_ICON_REMOVE', 'FILTER_TOOLTIP_REMOVE_FILTER' ]
, [ 'FIXED_ICON_REFRESH', 'FILTER_TOOLTIP_REFRESH' ]
])
                #print "FilterList="+str(FilterList)
                IconToFunction = { self.Core.Config.Get('FIXED_ICON_NOFLAG') : 'no_flag', self.Core.Config.Get('FIXED_ICON_UNSTRIKETHROUGH') : 'unseen', self.Core.Config.Get('FIXED_ICON_STRICKETHROUGH') : 'seen', self.Core.Config.Get('FIXED_ICON_NOTES') : 'notes' }
                return self.DrawReviewIconLinks(CounterList, IconToFunction, '', IdPrefix, True) # Add counters to filter

        def DrawImageFromConfigPair(self, ConfigList):
                FileName, ToolTip = self.Core.Config.GetAsList(ConfigList)
                return self.Render.DrawImage(FileName, { 'title' : ToolTip })

        def GetPluginDivId(self, Code, PluginType):
                # "Compression" attempt while keeping uniqueness:
                # First letter from plugin type is enough to make plugin div ids unique and predictable
                return MultipleReplace(Code, { 'OWASP' : 'O', 'OWTF' : 'F', '-' : '', '0' : '' })+PluginType[0]

        def DrawReviewButtons(self, DivId):
                return self.Render.DrawButtonJSLink( self.DrawImageFromConfigPair( [ 'FIXED_ICON_NOTES', 'REVIEW_TOOLTIP_NOTES' ]), "ToggleNotesBox('"+DivId+"')", { 'class' : 'icon' })+"&nbsp;" +self.Render.DrawButtonJSLink(self.DrawImageFromConfigPair( [ 'FIXED_ICON_STRICKETHROUGH', 'REVIEW_TOOLTIP_STRIKETHROUGH' ]), "MarkAsSeen('"+DivId+"')", { 'id' : 'l'+DivId, 'class' : 'icon' })+"&nbsp;" +self.DrawReviewIconLinks(self.Core.Config.Get('CHOSEN_ICONS_FOR_REVIEW').split(','), {}, DivId) +"&nbsp;".join(self.Render.DrawLinkPairs([ [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_REMOVE', 'REVIEW_TOOLTIP_REMOVE' ] ), "Rate('"+DivId+"', 'delete')" ] , [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_CLOSE_PLUGIN', 'REVIEW_TOOLTIP_CLOSE_PLUGIN' ] ), "HidePlugin('"+DivId+"')" ] ], 'DrawButtonJSLink', { 'class' : 'icon' }))

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
                DivId = self.GetPluginDivId(Plugin['Code'], Plugin['Type'])
                PluginReportPath = save_dir + "report.html"
                self.Core.CreateMissingDirs(save_dir)
                with open(PluginReportPath, 'w') as file: # 'w' is important to overwrite the partial report, necesary for scanners
                        Table = self.Render.CreateTable({ 'class' : 'report_intro' })
                        Table.CreateRow(['Plugin', 'Start', 'End', 'Runtime', 'Output Files'], True)
			Plugin['RunTime'] = self.Core.Timer.GetElapsedTimeAsStr('Plugin')
			Plugin['End'] = self.Core.Timer.GetEndDateTimeAsStr('Plugin')
                        Table.CreateRow([ Plugin['Type']+'/'+Plugin['File'], Plugin['Start'], Plugin['End'], Plugin['RunTime'], self.Core.Reporter.Render.DrawButtonLink('Browse Plugin Output Files', self.Core.GetPartialPath(save_dir)) ])
                        PluginHeader = '<h4 id="h'+DivId+'"><u>'+Plugin['Title']+'</u> - <i>'+Plugin['Type'].replace('_', ' ').upper()+'</i>'
                        PluginHeader += "&nbsp;" * 2 +self.DrawReviewButtons(DivId)+'</h4>'+Table.Render()
                        # Generate unique id every time to detect if plugin report changed to highlight modified stuff without losing review data (i.e. same plugin id):
                        PluginHeader += "<div id='token_"+DivId+"' style='display: none;'>"+self.Core.DB.GetNextHTMLID()+"</div>"
                        NotesBox = self.Render.CreateTable({ 'class' : 'report_intro' })
                        NotesBox.CreateRow(['Notes'], True)
                        # NOTE: autocomplete must be off because otherwise you see the text but is not saved in the review at all, which is counter-intuitive
                        NotesBox.CreateRow(['<textarea id="note_text_'+DivId+'" autocomplete="off" onChange="SaveComments(\''+DivId+'\')" rows=15 cols=150></textarea>'])
                        # Better with auto-save: NotesBox.CreateCustomRow('<tr><td align="right">'+self.Render.DrawButtonJSLink('<img src="images/floppy.png" />', "SaveComments('"+DivId+"')", { 'class' : 'icon' })+'</td></tr>')
                        PluginHeader += "<div id='notes_"+DivId+"' style='display: none;'>"+NotesBox.Render()+"</div><hr />"
                        file.write("\n"+PluginHeader+HTMLtext+"\n")
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
'TestGroupHeaderStr' : '<div id="'+TestGroup['Code']+'"><br />'+self.Render.DrawButtonLink(TestGroup['Descrip']+" ("+TestGroup['Code']+")", TestGroup['URL'], { 'class' : 'report_index' })+"&nbsp;"+TestGroup['Hint']
, 'RegisteredPlugins' : RegisteredPluginList } )
		return TestGroups

	def GetRegisteredAuxPlugins(self, ReportType): # Web Plugins go in OWASP Testing Guide order
		TestGroups = []
		for PluginType in sorted(self.Core.Config.Plugin.GetTypesForGroup('aux')): # Report aux plugins in alphabetical order
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

        def ReportFinish(self): # Group all partial reports (whether done before or now) into the final report
		Target = self.Core.Config.GetTarget()
		if not self.Core.DB.PluginRegister.NumPluginsForTarget(Target) > 0:
			cprint("No plugins completed for target, cannot generate report")
			return None # Must abort here, before report is generated
                self.ReportStart() # Wipe report
                with open(self.Core.Config.Get('HTML_DETAILED_REPORT_PATH'), 'a') as file:
		        file.write('<div id="GlobalReportButtonsTop" style="display:none;"></div>') # Start OWASP Testing Guide Item List
			AllPluginsTabIdList = []
			AllPluginsDivIdList = []
			for TestGroup in self.GetTestGroups(self.Core.Config.Get('REPORT_TYPE')):
		                HeaderStr = TestGroup['TestGroupHeaderStr']
				Tabs = self.Render.CreateTabs()
				for Match in  TestGroup['RegisteredPlugins']:
					PluginType = Match['Type']
					DivId = self.GetPluginDivId(Match['Code'], PluginType)
					Tabs.AddDiv(DivId, Match['Label'], open(Match['Path']).read())
					AllPluginsTabIdList.append(Tabs.GetTabIdForDiv(DivId))
					AllPluginsDivIdList.append(DivId)
				if Tabs.GetNumDivs() > 0:
					Tabs.CreateCustomTab('Results:') # First create custom tab, without javascript
					Tabs.CreateTabs() # Create the hide/show deal tabs
					Tabs.CreateTabButtons() # Add handy tab navigation buttons to the right
					HeaderStr += "&nbsp;" * 3 + ("&nbsp;" * 4).join(self.Render.DrawLinkPairs( [ [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_EXPAND_REPORT', 'NAV_TOOLTIP_EXPAND_REPORT' ]), "ClickLinkById('expand_report')" ], [ self.DrawImageFromConfigPair( [ 'FIXED_ICON_CLOSE_REPORT', 'NAV_TOOLTIP_CLOSE_REPORT' ]), "ClickLinkById('collapse_report')" ] ], 'DrawButtonJSLink', { 'class' : 'icon' }))
				HeaderStr += "<br />"
       				file.write(HeaderStr+Tabs.Render()+"</div>") # Save plugin reports in OWASP Guide order => 1 write per item = less memory-intensive
			if len(AllPluginsTabIdList) == 0:
				cprint("ERROR: No plugins found, cannot write report")
				return None # No plugins found (should not happe)
			UnhighlightReportPluginTabsJS = "SetClassNameToElems("+self.Render.DrawJSArrayFromList(AllPluginsTabIdList)+", '')"
			PluginDivs = self.Render.DrawJSArrayFromList(AllPluginsDivIdList)
			HideReportPluginDivsJS = UnhighlightReportPluginTabsJS+"; HideDivs("+PluginDivs+")"
			ShowReportPluginDivsJS = UnhighlightReportPluginTabsJS+"; ShowDivs("+PluginDivs+")"
			file.write("""
<br />
<div id='GlobalReportButtonsBottom' style='display:none;'>"""+self.Render.DrawButtonJSLink('+', ShowReportPluginDivsJS, { 'id' : 'expand_report' })+"&nbsp;"+self.Render.DrawButtonJSLink('-', HideReportPluginDivsJS, { 'id' : 'collapse_report' })+"""</div>
<script>
var AllPlugins = """+PluginDivs+"""
var Offset = '"""+self.Core.Config.Get('REVIEW_OFFSET')+"""'
"""+self.DrawJSCounterList()+"""
var DetailedReport = true
</script>
</body></html>""") # Closing HTML Report
			cprint("Report written to: "+self.Core.Config.Get('HTML_DETAILED_REPORT_PATH'))
			self.Core.DB.ReportRegister.Add(self.Core.Config.GetAsList( [ 'REVIEW_OFFSET', 'SUMMARY_HOST_IP', 'SUMMARY_PORT_NUMBER', 'HTML_DETAILED_REPORT_PATH', 'REPORT_TYPE' ] )) # Register report
			self.Summary.ReportFinish() # Build summary report

	def DrawJSCounterList(self):
		return """var AllCounters = """+self.Render.DrawJSArrayFromList(self.CounterList)

        def ReportWrite(self, html, text):
                cprint(text) # Text displayed on console only, html saved in report
                with open(self.Core.Config.Get('HTML_DETAILED_REPORT_PATH'), 'a') as file:
                        file.write(html) # Closing HTML Report

