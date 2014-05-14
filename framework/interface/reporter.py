#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pentesting
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com>
Twitter: @7a_ http://7-a.org
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
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The reporter module is in charge of producing the HTML Report as well as
 provide plugins with common HTML Rendering functions
'''

import cgi
import codecs
from tornado.template import Template, Loader
from framework.lib.general import *
# TODO: Check if this renderer is really necessary, change the name atleast
#from framework.interface.html import renderer
from framework.interface.html.filter import sanitiser
#from framework.report import summary

class Reporter:
    def __init__(self, CoreObj):
        self.Core = CoreObj  # Keep Reference to Core Object
        self.Init = False
        #self.Render = renderer.HTMLRenderer(self.Core)
        #self.Summary = summary.Summary(self.Core)
        self.Sanitiser = sanitiser.HTMLSanitiser()
        self.Loader = Loader(self.Core.Config.FrameworkConfigGet('POUTPUT_TEMPLATES_DIR'))
        self.mNumLinesToShow = 15
        self.CounterList = []

    def TransactionTableFromIDs(self, TransactionIDs, NumLinesReq=15, NumLinesRes=15):
        """ Draws a table of HTTP Transactions """
        # functions to get the first lines of a long string
        transactions = self.Core.DB.Transaction.GetByIDs(TransactionIDs)
        return self.Loader.load("transaction_table.html").generate(TransactionList = transactions)

    def TransactionTableForURLList( self, UseCache, URLList, Method = '', Data = '' ):
        transactions = self.Core.Requester.GetTransactions(UseCache, URLList, Method, Data)
        return self.Loader.load("transaction_table.html").generate(TransactionList = transactions)

    def unicode(self, *args):
        try:
            return unicode(*args)
        except TypeError:
            return args[0]  # Input is already Unicode

#----------------------------------- Methods exported from plugin_helper.py ---------------------------------

    def CommandTable( self, Command ):
        return self.Loader.load("command_table.html").generate(Command = Command)

    def LinkList( self, LinkListName, Links ): # Wrapper to allow rendering a bunch of links -without name- as resource links with name = link
        return self.Loader.load("link_list.html").generate(LinkListName = LinkListName, Links = Links)

    def ResourceLinkList( self, ResourceListName, ResourceList ): # Draws an HTML Search box for defined Vuln Search resources
        return self.Loader.load("resource_link_list.html").generate( ResourceListName = ResourceListName, ResourceList = ResourceList )

    def TabbedResourceLinkList(self, ResourcesList):
        # ResourceList = ["ResourceListName":[["Name1","Resource1"],["Name2","Resource2"]]]
        TabData = []
        Resources = []
        for ResourceListName, ResourceList in ResourcesList:
            TabID = ResourceListName.replace(' ','_')
            TabData.append([ResourceListName, TabID])
            Resources.append([TabID, ResourceList])
        return self.Loader.load("tabbed_resource_link_list.html").generate(TabData = TabData, Resources = Resources)

    def ListPostProcessing( self, ResourceListName, LinkList, HTMLLinkList ):
        return self.Loader.load("list_post_processing.html").generate( ResourceListName = ResourceListName, LinkList = LinkList, HTMLLinkList = HTMLLinkList )

    def RequestLinkList( self, ResourceListName, LinkList ):
        return self.Loader.load("request_link_list.html").generate( ResourceListName = ResourceListName, LinkList = LinkList )

    def VulnerabilitySearchBox( self, SearchStr ): # Draws an HTML Search box for defined Vuln Search resources
        VulnSearchResources = self.Core.DB.Resource.GetResources('VulnSearch')
        return self.Loader.load("vulnerability_search_box.html").generate(SearchStr=SearchStr, VulnSearchResources=VulnSearchResources, Count=len(VulnSearchResources))

    def SuggestedCommandBox( self, PluginOutputDir, CommandCategoryList, Header = '' ): # Draws HTML tabs for a list of TabName => Resource Group (i.e. how to run hydra, etc)
        return self.Loader.load("suggested_command_box.html").generate(Header = Header) #TODO: Fix up the plugin

    def CommandDump( self, Name, CommandIntro, ModifiedCommand, RelativeFilePath, OutputIntro, TimeStr):
    #def FormatCommandAndOutput( self, Name, CommandIntro, ModifiedCommand, FilePath, OutputIntro, OutputLines, TimeStr):
            #ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir = self.RunCommand( Command, PluginInfo, PluginOutputDir )
        AbsPath = self.Core.PluginHandler.RetrieveAbsPath(RelativeFilePath)
        OutputLines = open(AbsPath,"r").readlines()
        table_vars = {
                        "Name": Name,
                        "CommandIntro" : CommandIntro ,
                        "ModifiedCommand": ModifiedCommand,
                        "FilePath" : RelativeFilePath,
                        "OutputIntro":  OutputIntro,
                        "OutputLines": '\n'.join(OutputLines[0:self.mNumLinesToShow]) if (len(OutputLines) > self.mNumLinesToShow) else '\n'.join(OutputLines),
                        "TimeStr": TimeStr,
                        "mNumLinesToShow": (len(OutputLines) > self.mNumLinesToShow),
                }
        return self.Loader.load("command_dump.html").generate(**table_vars)

    def URLsFromStr(self, TimeStr, VisitURLs, URLList, NumFound):
        html_content = self.Loader.load("urls_from_str.html").generate(TimeStr=TimeStr,
                                                                VisitURLs=VisitURLs,
                                                                NumURLs=len(URLList),
                                                                NumFound=NumFound
                                                                )
        if URLList:
            html_content += self.LinkList("URLs Scraped", URLList)
        return html_content

    def Robots(self, NotStr, NumLines, NumAllow, NumDisallow, NumSitemap, SavePath, NumAddedURLs, EntriesList):
        vars = {
                         "NotStr":  NotStr,
                         "num_lines": NumLines, 
                         "num_allow": NumAllow,
                         "num_disallow": NumDisallow,
                         "num_sitemap": NumSitemap,
                         "save_path": SavePath,
                }
        TestResult =  self.Loader.load("robots.html").generate(**vars)
        if NumDisallow > 0 or NumAllow > 0 or NumSitemap > 0: # robots.txt contains some entries, show browsable list! :)
            for Display, Links in EntriesList:
                if Links: # Filters empty lists
                    TestResult += self.ResourceLinkList( Display, Links )
        TestResult += str(NumAddedURLs) + " URLs have been added and classified"
        return TestResult

    def DrawResponseMatchesTables( self, RegexpMatchResults, PluginInfo ):
        UniqueTable, AllTable = self.CreateMatchTables( 2 )
        #UniqueTable = "<h3>Unique Matches</h3><table class='transaction_log'>"+self.Core.Reporter.DrawTableRow(['ID', 'Links', 'Match'], True)
        #AllTable = "<h3>All Matches</h3><table class='transaction_log'>"+self.Core.Reporter.DrawTableRow(['ID', 'Links', 'Match'], True)
        Matches = []
        TransactionsMatched = []
        Command, SearchName, RegexpMatches = RegexpMatchResults
        for ID, Match in RegexpMatches:
                Row = [ID, self.Core.Reporter.DrawTransacLinksForID( ID, True ), cgi.escape( Match )]
                AllTable.CreateRow( Row )
                #Row = self.Core.Reporter.DrawTableRow([ID, self.Core.Reporter.DrawTransacLinksForID(ID, True), cgi.escape(Match)])
                #Row = self.Core.Reporter.DrawTableRow([self.Core.Reporter.Render.DrawButtonLink(ID, File, True, True), cgi.escape(Match)])
                if Match not in Matches:
                        Matches.append( Match )
                        UniqueTable.CreateRow( Row )
                        #UniqueTable += Row
                if ID not in TransactionsMatched:
                        TransactionsMatched.append( ID )
                #AllTable += Row
        #UniqueTable += "</table>"
        #AllTable += "</table>"
        NuTransactions, TotalTransac, Percentage, StatsStr = self.GetTransactionStats( len( TransactionsMatched ) )
        # NOTE: Table Creator does not support table structure below yet:
        SummaryTable = Template( """
        <h3> {{ SearchName }} </h3>
        <table>
                <tr>
                        <th>Stats</th>
                        <td>
                                <ul>
                                        <li> {{ Matches|count }} Unique  {{ SearchName }}  found</li>
                                        <li> {{ StatsStr }} transactions matched</li>
                                </ul>
                        </td>
                </tr>
                <tr>
                        <th> {{ SearchName }} </th>
                        <td class="alt">
                                <ul>
                                        <li>  <a href="{{ Unique_as_TEXTPath }}" class="button" target="_blank">
                                                        <span> Unique as TEXT </span>
                                                </a> </li>
                                        <li>  <a href="{{ Unique_as_HTMLPath }}" class="button" target="_blank">
                                                        <span> Unique as HTML </span>
                                                </a> </li>
                                        <li>  <a href="{{ All_as_HTMLPath }}" class="button" target="_blank">
                                                        <span> All as HTML </span>
                                                </a> </li>
                                </ul>
                        </td>
                </tr>
                <tr>
                        <th>Command</th><td> {{ Command|e }} </td>
                </tr>
                <tr>
                        <th>Log</th>
                        <td class="alt">
                                <a href="{{ HTMLTransacLogLink }}" class="button" target="_button">
                                        <span> See log </span>
                                </a> 
                        </td>
                </tr>
        </table>
""" )

        vars = {
                                "SearchName": SearchName,
                                "Matches": Matches,
                                "StatsStr":StatsStr,
                                "Command": Command,
                                "HTMLTransacLogLink": "../" + self.Core.Config.GetHTMLTransaclog( False ),
                                "Unique_as_TEXTPath": "../" + self.DumpFile( 'unique' + WipeBadCharsForFilename( SearchName ) + '.txt', "\n".join( Matches ), PluginInfo, 'Unique as TEXT' )[0],
                                "Unique_as_HTMLPath": "../" + self.DumpFile( 'unique' + WipeBadCharsForFilename( SearchName ) + '.html', "<h3>Unique Matches</h3>" + UniqueTable.Render(), PluginInfo, 'Unique as HTML' )[0],
                                "All_as_HTMLPath": "../" + self.DumpFile( 'all' + WipeBadCharsForFilename( SearchName ) + '.html', "<h3>All Matches</h3>" + AllTable.Render(), PluginInfo, 'All as HTML' )[0] ,
                        }
        return SummaryTable.render(vars)

    def CookieAttributeAnalysis( self, CookieValueList, Header2TransacDict ):
        vars = {
                "Cookies": [
                                        {
                                                "Name": Cookie.split( '=' )[0],
                                                "Link":  Header2TransacDict[self.Core.Config.Get( 'HEADERS_FOR_COOKIES' ).lower() + Cookie],
                                                "Attribs": Cookie.replace( Cookie.split( '=' )[0] + "=", "" ).replace( "; ", ";" ).split( ";" ),
                                        } for Cookie in CookieValueList
                                   ],
                }
        Table = self.Core.Reporter.Render.CreateTable( {'class' : 'report_intro'} )
        SetCookie = self.Core.Config.Get( 'HEADERS_FOR_COOKIES' ).lower()
        PossibleCookieAttributes = self.Core.Config.Get( 'COOKIE_ATTRIBUTES' ).split( ',' )
        for Cookie in CookieValueList:
                CookieName = Cookie.split( '=' )[0]
                CookieLink = self.Core.Reporter.Render.DrawButtonLink( cgi.escape( CookieName ), Header2TransacDict[SetCookie + Cookie] )
                CookieAttribs = Cookie.replace( CookieName + "=", "" ).replace( "; ", ";" ).split( ";" )
                #Table.CreateRow(["Cookie: "+CookieLink], True, { 'colspan' : '2' })
                Table.CreateCustomRow( '<tr><th colspan="2">' + "Cookie: " + CookieLink + '</th></tr>' )
                Table.CreateRow( ['Attribute', 'Value'], True )
                #Table += "<th colspan='2'>Cookie: "+CookieLink+"</th>"
                #Table += self.Core.Reporter.DrawTableRow(['Attribute', 'Value'], True)
                NotFoundStr = "<b>Not Found</b>"
                if CookieAttribs[0]:
                        CookieValue = CookieAttribs[0]
                else:
                        CookieValue = NotFoundStr
                Table.CreateRow( ['Value', CookieValue] )
                #Table += self.Core.Reporter.DrawTableRow(['Value', ])
                for Attrib in PossibleCookieAttributes:
                        DisplayAttribute = NotFoundStr
                        for PresentAttrib in CookieAttribs:
                                if PresentAttrib.lower().startswith( Attrib.lower() ): # Avoid false positives due to cookie contents
                                        DisplayAttribute = PresentAttrib
                                        break
                        Table.CreateRow( [Attrib, DisplayAttribute] )
                        #Table += self.Core.Reporter.DrawTableRow([Attrib, DisplayAttribute])
        if Table.GetNumRows() == 0:
                return "" # No Attributes found
        return "<h3>Cookie Attribute Analysis</h3>" + Table.Render()
        #Table = "<h3>Cookie Attribute Analysis</h3><table class='report_intro'>"+Table+"</table>"
        #return Table

    def ResearchHeaders( self, RegexName ):
        regex_name, matched_transactions, num_matched_in_scope = self.Core.DB.Transaction.SearchByRegexName(RegexName)
        # [[regex_name, matched_transactions, num_matched_in_scope]]
        if int(num_matched_in_scope):
            MatchedPercent = (len(matched_transactions)/int(num_matched_in_scope))*100
        else:
            MatchedPercent = 0
        Matches = []
        for transaction in matched_transactions:
            Matches += transaction.GrepByRegexName(regex_name)
        UniqueMatches = map(list, set(map(tuple, Matches)))
        # [[unique_matches, matched_transactions, matched_percentage]]
        return [self.Loader.load("header_searches.html").generate(MatchedPercent = MatchedPercent, UniqueMatches = UniqueMatches), UniqueMatches] #TODO: Activate links for values

    def FingerprintData(self):
        HeaderTable, UniqueMatches = self.ResearchHeaders('HEADERS_FOR_FINGERPRINT')
        for Header,Value in UniqueMatches:
                HeaderTable += self.VulnerabilitySearchBox(Value) # Add Vulnerability search boxes after table
        return HeaderTable

    def Html(self, HtmlString):
        return(HtmlString)
