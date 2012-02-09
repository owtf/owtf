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

This module contains helper functions to make plugins simpler to read and write, centralising common functionality easy to reuse
'''
import os, re, cgi
from framework.lib.general import *
from collections import defaultdict

class PluginHelper:
	mNumLinesToShow = 25

	def __init__(self, CoreObj):
		self.Core = CoreObj
		# Compile regular expressions only once on init:
                self.RobotsAllowRegexp = re.compile("Allow: ([^\n  #]+)")
                self.RobotsDisallowRegexp = re.compile("Disallow: ([^\n #]+)")
		self.RobotsSiteMap = re.compile("Sitemap: ([^\n #]+)")

	def MultipleReplace(self, Text, ReplaceDict): # This redundant method is here so that plugins can use it
		return MultipleReplace(Text, ReplaceDict)

	def DrawLinkList(self, LinkListName, Links): # Wrapper to allow rendering a bunch of links -without name- as resource links with name = link
		ResourceLikeLinks = []
		for Link in Links: 
			ResourceLikeLinks.append([Link, Link])
		return self.DrawResourceLinkList(LinkListName, ResourceLikeLinks)

        def DrawResourceLinkList(self, ResourceListName, ResourceList): # Draws an HTML Search box for defined Vuln Search resources
                LinkList = []
                HTMLLinkList = [] 
                for Name, Resource in ResourceList:
                        URL = MultipleReplace(Resource.strip(), self.Core.Config.GetReplacementDict()).replace('"', '%22')
                        LinkList.append(URL)
			cprint("Generating link for "+Name+"..") # Otherwise there would be a lovely python exception and we would not be here :)
                        HTMLLinkList.append(self.Core.Reporter.Render.DrawButtonLink(Name, URL))
		return self.DrawListPostProcessing(ResourceListName, LinkList, HTMLLinkList)

	def DrawListPostProcessing(self, ResourceListName, LinkList, HTMLLinkList):
                Content = '<hr />'+ResourceListName+': '
                if len(LinkList) > 1: # Open All In Tabs only makes sense if num items > 1
                        Content += self.Core.Reporter.Render.DrawButton('Open All In Tabs', "OpenAllInTabs(new Array('"+"','".join(LinkList)+"'))")
		Content += self.Core.Reporter.Render.DrawHTMLList(HTMLLinkList)
                return Content

	def RequestAndDrawLinkList(self, ResourceListName, ResourceList, PluginInfo):
	        #for Name, Resource in Core.Config.GetResources('PassiveRobotsAnalysisHTTPRequests'):
                LinkList = []
                HTMLLinkList = [] 
	        for Name, Resource in ResourceList:
			Chunks = Resource.split('###POST###')
			URL = Chunks[0]
			POST = None
			Method = 'GET'
			if len(Chunks) > 1: # POST
				Method = 'POST'
				POST = Chunks[1]
	                Transaction = self.Core.Requester.GetTransaction(True, URL, Method, POST)
			if Transaction.Found:
				Path, HTMLLink = self.SaveSandboxedTransactionHTML(Name, Transaction, PluginInfo)
				HTMLLinkList.append(HTMLLink)
				LinkList.append(Path)
		return self.DrawListPostProcessing(ResourceListName, LinkList, HTMLLinkList)

	def SaveSandboxedTransactionHTML(self, Name, Transaction, PluginInfo): # 1st filters HTML, 2nd builds sandboxed iframe, 3rd give link to sandboxed content
		RawHTML = Transaction.GetRawResponseBody()
		#print "RawHTML="+RawHTML
		FilteredHTML = self.Core.Reporter.Sanitiser.CleanThirdPartyHTML(RawHTML)
		#print "FilteredHTML="+FilteredHTML
		NotSandboxedPath, Discarded = self.DumpFile("NOT_SANDBOXED_"+Name+".html", FilteredHTML, PluginInfo, Name)
		SandboxedPath, HTMLLink = self.DumpFile("SANDBOXED_"+Name+".html", self.Core.Reporter.Render.DrawiFrame( { 'src' : NotSandboxedPath.split('/')[-1], 'sandbox' : '',  'security' : 'restricted', 'width' : '100%', 'height' : '100%', 'frameborder' : '0', 'style' : "overflow-y:auto; overflow-x:hidden;" } ), PluginInfo, Name)
		return [ SandboxedPath, HTMLLink ]

        def DrawVulnerabilitySearchBox(self, SearchStr): # Draws an HTML Search box for defined Vuln Search resources
                ProductId = 'prod'+self.Core.DB.GetNextHTMLID() # Keep product id unique among different search boxes (so that Javascript works)
                Count = 0
                CellStr = ''
                SearchAll = []
                for Name, Resource in self.Core.Config.GetResources('VulnSearch'):
                        LinkStart, LinkFinish = Resource.split('@@@PLACE_HOLDER@@@')
                        LinkStart = LinkStart.strip()
                        LinkFinish = LinkFinish.strip()
                        JavaScript = "window.open('"+LinkStart+"'+GetById('"+ProductId+"').value+'"+LinkFinish+"')"
                        SearchAll.append(JavaScript)
                        CellStr += '<td>'+self.Core.Reporter.Render.DrawButton(Name, JavaScript)+'</td>'
                        Count += 1
                VulnSearch = """
<table>
        <tr>
                <th colspan="""+str(Count)+""">
                        Search for Vulnerabilities: <input name="product" id='"""+ProductId+"""' type="text" size="35" value='"""+SearchStr+"""'>
                        <button onclick="javascript:"""+';'.join(SearchAll)+"""">Search All</button>
                </th>
        </tr>
        <tr>
                """+str(CellStr)+"""
        </tr>
"""
                VulnSearch += '</table><hr />'
                return VulnSearch

	def DrawSuggestedCommandBox(self, PluginInfo, CommandCategoryList, Header = ''): # Draws HTML tabs for a list of TabName => Resource Group (i.e. how to run hydra, etc)
		cprint("Drawing suggested command box..")
		if Header == '': # Default header if not supplied
			Header = "Suggested potentially interesting commands"
		Header = "<hr /><h4>"+Header+"</h4>"
		Tabs = self.Core.Reporter.Render.CreateTabs()
		PluginOutputDir = self.InitPluginOutputDir(PluginInfo)
		for Tab, ResourceGroup in CommandCategoryList:
			Table = self.Core.Reporter.Render.CreateTable({'class' : 'run_log'})
		        for Name, Resource in self.Core.Config.GetResources(ResourceGroup):
                		Table.CreateRow([Name], True)
				ModifiedCommand = self.Core.Shell.GetModifiedShellCommand(Resource.strip(), PluginOutputDir) # Replaces the plugin output dir, etc
                		Table.CreateRow( [ self.Core.Reporter.DrawCommand(self.MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict())) ] )
                		#Table.CreateRow([cgi.escape(self.MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict()))])
			Tabs.AddDiv(Tab.replace(' ', '_').lower(), Tab, Table.Render())
		Tabs.CreateTabs()
                Tabs.CreateTabButtons()
		return Header+Tabs.Render()

	def SetConfigPluginOutputDir(self, PluginInfo):
                PluginOutputDir = self.Core.PluginHandler.GetPluginOutputDir(PluginInfo)
                self.Core.Config.Set('PLUGIN_OUTPUT_DIR', os.getcwd()+'/'+PluginOutputDir) # FULL output path for plugins to use
		self.Core.Shell.RefreshReplacements() # Get dynamic replacement, i.e. plugin-specific output directory
		return PluginOutputDir

	def InitPluginOutputDir(self, PluginInfo):
		PluginOutputDir = self.SetConfigPluginOutputDir(PluginInfo)
                self.Core.CreateMissingDirs(PluginOutputDir) # Create output dir so that scripts can cd to it :)
		return PluginOutputDir

	def RunCommand(self, Command, PluginInfo, PluginOutputDir):
		FrameworkAbort = PluginAbort = False
		if not PluginOutputDir:
			PluginOutputDir = self.InitPluginOutputDir(PluginInfo)
               	self.Core.Timer.StartTimer('FormatCommandAndOutput')
		ModifiedCommand = self.Core.Shell.GetModifiedShellCommand(Command, PluginOutputDir)
		try:
	                RawOutput = self.Core.Shell.shell_exec_monitor(ModifiedCommand)
		except PluginAbortException, PartialOutput:
			RawOutput = str(PartialOutput.parameter) # Save Partial Output
			PluginAbort = True
		except FrameworkAbortException, PartialOutput:
			RawOutput = str(PartialOutput.parameter) # Save Partial Output
			FrameworkAbort = True

                TimeStr = self.Core.Timer.GetElapsedTimeAsStr('FormatCommandAndOutput')
                cprint("Time="+TimeStr)
		return [ ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir ]

	def GetCommandOutputFileNameAndExtension(self, InputName):
		OutputName = InputName
		OutputExtension = "txt"
		if InputName.split('.')[-1] in [ 'html' ]:
			OutputName = InputName[0:-5]
			OutputExtension = "html"
		return [ OutputName, OutputExtension ]

	def TruncateOutput(self, FilePath, RawOutput, OutputLines):
                TruncationWarningLinkToFile = self.Core.Reporter.Render.DrawButtonLink('Click here to see all output!', FilePath, {}, True)
                BottomNote = ''
		NewLine = "\n" 
                if len(OutputLines) > self.mNumLinesToShow: #Show first few lines of command, rest in file
                	Snippet = NewLine.join(OutputLines[0:self.mNumLinesToShow])
	                BottomNote = NewLine+"<b>NOTE: Output longer than "+str(self.mNumLinesToShow)+" lines, "+TruncationWarningLinkToFile+"</b>"
                else: # Output fits in NumLinesToShow
       	        	Snippet = RawOutput
		return [ BottomNote, Snippet ]

	def EscapeSnippet(self, Snippet, Extension):
		if Extension == "html": # HTML
			return str(Snippet)
		return cgi.escape(str(Snippet)) # Escape snippet to avoid breaking HTML

	def FormatCommandAndOutput(self, CommandIntro, OutputIntro, Name, Command, PluginInfo, PluginOutputDir = ''):
		ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir = self.RunCommand(Command, PluginInfo, PluginOutputDir)
		Table = self.Core.Reporter.Render.CreateTable({'class' : 'commanddump'})
		Table.CreateRow( [ CommandIntro ], True)
		#Table.CreateRow( [ cgi.escape(str(ModifiedCommand)).replace(';', '<br />') ] ) 
		Table.CreateRow( [ self.Core.Reporter.DrawCommand(ModifiedCommand) ] ) 
                OutputLines = RawOutput.split("\n")
		Name, Extension = self.GetCommandOutputFileNameAndExtension(Name)
                FilePath = self.Core.PluginHandler.DumpPluginFile(Name+"."+Extension, RawOutput, PluginInfo)
                LinkToFile = self.Core.Reporter.Render.DrawButtonLink(Name, FilePath, {}, True)
		BottomNote, Snippet = self.TruncateOutput(FilePath, RawOutput, OutputLines)
		Table.CreateRow( [ LinkToFile+" "+OutputIntro+" (Execution Time: "+TimeStr+")" ], True)
		Table.CreateRow( [ "<pre>"+self.EscapeSnippet(Snippet, Extension)+"<br />"+BottomNote+"</pre>" ] )
		return [ PluginAbort, FrameworkAbort, Table.Render(), RawOutput ]

	def LogURLsFromStr(self, RawOutput):
		self.Core.Timer.StartTimer('LogURLsFromStr')
		URLList = RawOutput.strip().split("\n")
		self.Core.DB.URL.ImportURLs(URLList) # Extract and classify URLs and store in DB
		NumFound = 0
		VisitURLs = False
		if self.Core.PluginHandler.IsActiveTestingPossible(): # Can visit new URLs found to feed DB straightaway
			VisitURLs = True 
			for Transaction in self.Core.Requester.GetTransactions(True, self.Core.DB.URL.GetURLsToVisit(URLList)): # Visit all URLs if not in Cache
				if Transaction.Found:
					NumFound += 1
		TimeStr = self.Core.Timer.GetElapsedTimeAsStr('LogURLsFromStr')
                cprint("Spider/URL scaper time="+TimeStr)
		Table = self.Core.Reporter.Render.CreateTable({'class' : 'commanddump'})
		Table.CreateCustomRow('<tr><th colspan="2">Spider/URL scraper</th></tr>')
		Table.CreateRow(['Time', 'URL stats'], True)
                Table.CreateRow([TimeStr, self.Core.Reporter.Render.DrawHTMLList(['Visited URLs?: '+str(VisitURLs), str(len(URLList))+' URLs scraped', str(NumFound)+' URLs found'])])
		return Table.Render()

        def DrawCommandDump(self, CommandIntro, OutputIntro, ResourceList, PluginInfo, PreviousOutput, NumLinesToShow = 25):
		self.mNumLinesToShow = NumLinesToShow
		PluginOutputDir = self.InitPluginOutputDir(PluginInfo)
                #Content = LinkToPluginOutputDir = '<br />'+self.Core.Reporter.Render.DrawButtonLink('Browse Plugin Output Files', self.Core.GetPartialPath(PluginOutputDir))+'<br />' <- This is now in the Plugin report box
		Content = ""
                for Name, Command in ResourceList: #Command = Resource.strip()
			PluginAbort, FrameworkAbort, HTMLContent, RawOutput = self.FormatCommandAndOutput(CommandIntro, OutputIntro, Name, Command, PluginInfo, PluginOutputDir)
			Content += HTMLContent
			if Name == self.Core.Config.Get('EXTRACT_URLS_RESERVED_RESOURCE_NAME'): # This command returns URLs for processing
				Content += self.LogURLsFromStr(RawOutput)
                        if self.Core.Config.Get('UPDATE_REPORT_AFTER_EACH_COMMAND') == 'Yes':
                                self.Core.Reporter.SavePluginReport(Content, PluginInfo) # Keep updating the report after each command/scanner runs
			if PluginAbort: # Pass partial output to external handler:
				raise PluginAbortException(PreviousOutput+Content)
			if FrameworkAbort:
				raise FrameworkAbortException(PreviousOutput+Content)
                return Content

	def DumpFile(self, Filename, Contents, PluginInfo, LinkName = ''):
                save_path = self.Core.PluginHandler.DumpPluginFile(Filename, Contents, PluginInfo)
		if not LinkName:
			LinkName = save_path
		cprint("File: "+Filename+" saved to: "+save_path)
                return [ save_path, self.Core.Reporter.Render.DrawButtonLink(LinkName, save_path, {}, True) ]

	def DumpFileGetLink(self, Filename, Contents, PluginInfo, LinkName = ''):
		return self.DumpFile(Filename, Contents, PluginInfo, LinkName)[0]

	def AnalyseRobotsEntries(self, Contents): # Find the entries of each kind and count them
                num_lines = len(Contents.split("\n")) # Total number of robots.txt entries
                AllowedEntries = self.RobotsAllowRegexp.findall(Contents)
                num_allow = len(AllowedEntries) # Number of lines that start with "Allow:"
		DisallowedEntries = self.RobotsDisallowRegexp.findall(Contents)
                num_disallow = len(DisallowedEntries) # Number of lines that start with "Disallow:"
		SitemapEntries = self.RobotsSiteMap.findall(Contents)
                num_sitemap = len(SitemapEntries) # Number of lines that start with "Sitemap:"
		NotStr = ''
		if 0 == num_allow and 0 == num_disallow and 0 == num_sitemap:
			NotStr = 'NOT '
		return [ num_lines, AllowedEntries, num_allow, DisallowedEntries, num_disallow, SitemapEntries, num_sitemap , NotStr ]

	def ProcessRobots(self, PluginInfo, Contents, LinkStart, LinkEnd, Filename = 'robots.txt'):
		num_lines, AllowedEntries, num_allow, DisallowedEntries, num_disallow, SitemapEntries, num_sitemap, NotStr = self.AnalyseRobotsEntries(Contents)
                save_path = self.Core.PluginHandler.DumpPluginFile(Filename, Contents, PluginInfo)
                TestResult = "robots.txt was "+NotStr+"found. "+str(num_lines)+" lines: "+str(num_allow)+" Allowed, "+str(num_disallow)+" Disallowed, "+str(num_sitemap)+" Sitemap.\n"
                TestResult += '<br />Saved to: '+self.Core.Reporter.Render.DrawButtonLink(save_path, save_path, {}, True)#<a href="'+save_path+'" target="_blank">'+save_path+'</a>'
		TopURL = self.Core.Config.Get('TOP_URL')
                if num_disallow > 0 or num_allow > 0 or num_sitemap > 0: # robots.txt contains some entries, show browsable list! :)
			self.Core.DB.URL.AddURLsStart()
			for Display, Entries in [ [ 'Disallowed Entries', DisallowedEntries ], [ 'Allowed Entries', AllowedEntries ], [ 'Sitemap Entries', SitemapEntries ] ]:
	                        Links = [] # Initialise category-specific link list
	                        for Entry in Entries:
					if 'Sitemap Entries' == Display:
						URL = Entry
						self.Core.DB.URL.AddURL(URL) # Store real links in the DB
						Links.append( [ Entry, Entry ] ) # Show link in defined format (passive/semi_passive)
					else:
						URL = TopURL+Entry
						self.Core.DB.URL.AddURL(URL) # Store real links in the DB
						Links.append( [ Entry, LinkStart+Entry+LinkEnd ] ) # Show link in defined format (passive/semi_passive)
	                        TestResult += self.Core.PluginHelper.DrawResourceLinkList(Display, Links)
			TestResult += self.Core.DB.URL.AddURLsEnd()
                cprint("robots.txt was "+NotStr+"found")
		return TestResult
	
	def LogURLs(self, PluginInfo, ResourceList):
		return "Is this called?"
		NumURLsBefore = self.Core.DB.URL.GetNumURLs()
		for Name, Command in ResourceList: #Command = Resource.strip()
			HTMLOutput, RawOutput = self.FormatCommandAndOutput('Extract Links Command', 'Extract Links Output', Name, Command, PluginInfo)
			self.LogURLsFromStr(RawOutput)
                        #for line in RawOutput.split("\n"):
			#	self.Core.DB.URL.AddURL(line.strip())
		self.Core.DB.SaveAllDBs() # Save URL DBs to disk
		NumURLsAfter = self.Core.DB.URL.GetNumURLs()
		Message = cprint(str(NumURLsAfter-NumURLsBefore)+" URLs have been added and classified")
		return HTMLOutput+"<br />"+Message

	def DrawTransactionTableForURLList(self, UseCache, URLList, Method = '', Data = ''):
		return self.Core.Reporter.DrawHTTPTransactionTable(self.Core.Requester.GetTransactions(UseCache, URLList, Method, Data))

	def GetTransactionStats(self, NumMatchedTransactions):
                TotalTransac = self.Core.DB.Transaction.GetNumTransactionsInScope()
		Percentage = round(NumMatchedTransactions * 100 / max(TotalTransac,1), 2)
		StatsStr = str(NumMatchedTransactions)+" out of "+str(TotalTransac)+" ("+str(Percentage)+"%)"
		return [ NumMatchedTransactions, TotalTransac, Percentage, StatsStr ]

	def CreateMatchTable(self):
		Table = self.Core.Reporter.Render.CreateTable({'class' : 'transaction_log'})	
		Table.CreateRow(['ID', 'Links', 'Match'], True)
		return Table
	
	def CreateMatchTables(self, Num):
		TableList = []
		for x in range(0, Num):
			TableList.append(self.CreateMatchTable())
		return TableList

	def DrawResponseMatchesTables(self, RegexpMatchResults, PluginInfo):
		UniqueTable, AllTable = self.CreateMatchTables(2)
		#UniqueTable = "<h3>Unique Matches</h3><table class='transaction_log'>"+self.Core.Reporter.DrawTableRow(['ID', 'Links', 'Match'], True)
		#AllTable = "<h3>All Matches</h3><table class='transaction_log'>"+self.Core.Reporter.DrawTableRow(['ID', 'Links', 'Match'], True)
		Matches = []
		TransactionsMatched = []
		Command, SearchName, RegexpMatches = RegexpMatchResults
		for ID, Match in RegexpMatches:
			Row = [ID, self.Core.Reporter.DrawTransacLinksForID(ID, True), cgi.escape(Match)]
			AllTable.CreateRow(Row)
			#Row = self.Core.Reporter.DrawTableRow([ID, self.Core.Reporter.DrawTransacLinksForID(ID, True), cgi.escape(Match)])
			#Row = self.Core.Reporter.DrawTableRow([self.Core.Reporter.Render.DrawButtonLink(ID, File, True, True), cgi.escape(Match)])
			if Match not in Matches:
				Matches.append(Match)
				UniqueTable.CreateRow(Row)
				#UniqueTable += Row
			if ID not in TransactionsMatched:
				TransactionsMatched.append(ID)
			#AllTable += Row
		#UniqueTable += "</table>"
		#AllTable += "</table>"
		NuTransactions, TotalTransac, Percentage, StatsStr = self.GetTransactionStats(len(TransactionsMatched))
		# NOTE: Table Creator does not support table structure below yet:
		SummaryTable = """
<h3>"""+SearchName+"""</h3>
<table>
	<tr>
		<th>Stats</th>
		<td>
			<ul>
				<li>"""+str(len(Matches))+""" Unique """+SearchName+""" found</li>
				<li>"""+StatsStr+""" transactions matched</li>
			</ul>
		</td>
	</tr>
	<tr>
		<th>"""+SearchName+"""</th>
		<td class="alt">
			<ul>
				<li>"""+self.DumpFileGetLink('unique'+WipeBadCharsForFilename(SearchName)+'.txt', "\n".join(Matches), PluginInfo, 'Unique as TEXT')+"""</li>
				<li>"""+self.DumpFileGetLink('unique'+WipeBadCharsForFilename(SearchName)+'.html', "<h3>Unique Matches</h3>"+UniqueTable.Render(), PluginInfo, 'Unique as HTML')+"""</li>
				<li>"""+self.DumpFileGetLink('all'+WipeBadCharsForFilename(SearchName)+'.html', "<h3>All Matches</h3>"+AllTable.Render(), PluginInfo, 'All as HTML')+"""</li>
			</ul>
		</td>
	</tr>
	<tr>
		<th>Command</th><td>"""+self.Core.Reporter.DrawCommand(Command)+"""</td>
	</tr>
	<tr>
		<th>Log</th><td class="alt">"""+self.Core.Reporter.Render.DrawButtonLink('See log', self.Core.Config.GetHTMLTransacLog(True))+"""</td>
	</tr>
</table>
"""
		return SummaryTable

	def FindMultilineResponseMatchesForRegexp(self, ResponseRegexp, PluginInfo):
		return self.DrawResponseMatchesTables(self.Core.DB.Transaction.GrepMultiLineResponseRegexp(ResponseRegexp), PluginInfo)

	def FindMultilineResponseMatchesForRegexps(self, ResponseRegexpList, PluginInfo):
		Result = ""
		for ResponseRegexp in ResponseRegexpList:
			#print "ResponseRegexp="+str(ResponseRegexp)
			Result += self.FindMultilineResponseMatchesForRegexp(ResponseRegexp, PluginInfo) 
		return Result

	def FindHeaders(self, HeaderList):
		HeaderDict = defaultdict(list)
		HeaderLines = []
		AllValues = []
		Header2TransacDict = {}
		TransactionFiles = []
		Command, Headers = self.Core.DB.Transaction.GrepHeaders(HeaderList)
		for Header in Headers.split("\n"):
			TransacFile = Header.split(":")[0]
			HeaderLine = Header.replace(TransacFile+":", "").strip()
			if not HeaderLine:
				continue #Skip blank lines
			HeaderName = HeaderLine.split(':')[0] 
			HeaderValue = HeaderLine.replace(HeaderName+": ", "").strip() # Replace respecting case!
			if 'No such file or directory' == HeaderValue:
				continue # Skip garbage errors
			if TransacFile not in TransactionFiles: # Count unique transactions
				TransactionFiles.append(TransacFile)
			if HeaderLine in HeaderLines:
				continue # Skip already processed headers
			HeaderLines.append(HeaderLine)
			HeaderName = HeaderName.lower() # Now force lowercase to ensure match later!
			HeaderDict[HeaderName].append(HeaderValue)
			AllValues.append(HeaderValue)
			Header2TransacDict[HeaderName+HeaderValue] = TransacFile
		return [ Command, HeaderDict, AllValues, Header2TransacDict , len(TransactionFiles) ]

	def ResearchHeaders(self, HeaderList):
		Command, HeaderDict, AllValues, Header2TransacDict, NuTransactions = self.FindHeaders(HeaderList)
		NuTransactions, TotalTransac, Percentage, StatsStr = self.GetTransactionStats(NuTransactions)
		Table = '<h3>Header Analysis Summary</h3>'
		Table += "<table>" # NOTE: Table structure not supported by table creator
		Table += "<tr><th>Log</th><td>"+self.Core.Reporter.Render.DrawButtonLink('See log', self.Core.Config.GetHTMLTransacLog(True))+"</td></tr>"
		Table += "<tr><th>HTTP Transaction Stats</th><td class='alt'>"+StatsStr+" matched"+"</td></tr>"
		Table += "<tr><th>Analysis Command</th><td>"+self.Core.Reporter.DrawCommand(Command)+"</td></tr>"
		#Table += self.Core.Reporter.DrawTableRow(['Log', 'HTTP Transaction Stats', 'Command'], True)
		#Table += self.Core.Reporter.DrawTableRow([self.Core.Reporter.Render.DrawButtonLink('See log', self.Core.Config.GetHTMLTransacLog(True)), str(NuTransactions)+" out of "+str(TotalTransac)+" ("+str(Percentage)+"%) matches", cgi.escape(Command)])
#		Table = "Header Value Analysis: "+str(NuTransactions)+" out of "+str(TotalTransac)+" ("+str(Percentage)+"%) HTTP transaction(s) matched "+self.Core.Reporter.Render.DrawButtonLink('See log', self.Core.Config.GetHTMLTransacLog(True))+":<br />"
#		Table += "Command used to investigate headers: "+cgi.escape(Command)+"<br />"
		Table += "</table>"
		Table += '<h3>Header Value Analysis</h3>'
		Table += '<p>NOTE: Only <u>unique values per header</u> are shown with a link to an example transaction</p>'
		HTable = self.Core.Reporter.Render.CreateTable({'class' : 'report_intro'})
		#Table += "<table class='report_intro'>"
		#Table += self.Core.Reporter.DrawTableRow(['Header', 'Values'], True)
		HTable.CreateRow(['Header', 'Values'], True)
		for Header in HeaderList:
			LHeader = Header.lower() # Force lowercase to ensure match
			if LHeader not in HeaderDict:
				#Table += self.Core.Reporter.DrawTableRow([cgi.escape(Header), "Not Found"])
				HTable.CreateRow([cgi.escape(Header), "Not Found"])
			else: # Header found
				LinkList = [] 
				for Value in HeaderDict[LHeader]:
					LinkList.append(self.Core.Reporter.Render.DrawButtonLink(cgi.escape(Value), Header2TransacDict[LHeader+Value]))
				#Table += self.Core.Reporter.DrawTableRow([cgi.escape(Header), "<br />".join(LinkList)])
				HTable.CreateRow([cgi.escape(Header), "<br />".join(LinkList)])
		#Table += "</table>"
		Table += HTable.Render() # Append header table at the end of the string
		return [ AllValues, Table, HeaderDict, Header2TransacDict , NuTransactions ]

	def CookieAttributeAnalysis(self, CookieValueList, Header2TransacDict):
		Table = self.Core.Reporter.Render.CreateTable({'class' : 'report_intro'})
		SetCookie = self.Core.Config.Get('HEADERS_FOR_COOKIES').lower()
		PossibleCookieAttributes = self.Core.Config.Get('COOKIE_ATTRIBUTES').split(',')
		for Cookie in CookieValueList:
			CookieName = Cookie.split('=')[0]
			CookieLink = self.Core.Reporter.Render.DrawButtonLink(cgi.escape(CookieName), Header2TransacDict[SetCookie+Cookie])
			CookieAttribs = Cookie.replace(CookieName+"=", "").replace("; ", ";").split(";")
			#Table.CreateRow(["Cookie: "+CookieLink], True, { 'colspan' : '2' })
			Table.CreateCustomRow('<tr><th colspan="2">'+"Cookie: "+CookieLink+'</th></tr>')
			Table.CreateRow(['Attribute', 'Value'], True)
			#Table += "<th colspan='2'>Cookie: "+CookieLink+"</th>"
			#Table += self.Core.Reporter.DrawTableRow(['Attribute', 'Value'], True)
			NotFoundStr = "<b>Not Found</b>"
			if CookieAttribs[0]:
				CookieValue = CookieAttribs[0]
			else:
				CookieValue = NotFoundStr
			Table.CreateRow(['Value', CookieValue])
			#Table += self.Core.Reporter.DrawTableRow(['Value', ])
			for Attrib in PossibleCookieAttributes:
				DisplayAttribute = NotFoundStr
				for PresentAttrib in CookieAttribs:
					if PresentAttrib.lower().startswith(Attrib.lower()): # Avoid false positives due to cookie contents
						DisplayAttribute = PresentAttrib
						break
				Table.CreateRow([Attrib, DisplayAttribute])
				#Table += self.Core.Reporter.DrawTableRow([Attrib, DisplayAttribute])
		if Table.GetNumRows() == 0:
			return "" # No Attributes found
		return "<h3>Cookie Attribute Analysis</h3>"+Table.Render()
		#Table = "<h3>Cookie Attribute Analysis</h3><table class='report_intro'>"+Table+"</table>"
		#return Table
					
	def ResearchFingerprintInLog(self):
		cprint("Researching Fingerprint in Log ..")
		AllValues, HeaderTable , HeaderDict, Header2TransacDict, NuTransactions = self.ResearchHeaders(self.Core.Config.GetHeaderList('HEADERS_FOR_FINGERPRINT'))
	        for Value in AllValues:
			HeaderTable += self.DrawVulnerabilitySearchBox(Value) # Add Vulnerability search boxes after table
	        return HeaderTable 

