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
from framework.interface.html.filter import sanitiser


class Reporter:
    def __init__(self, CoreObj):
        self.Core = CoreObj  # Keep Reference to Core Object
        self.Init = False
        self.Sanitiser = sanitiser.HTMLSanitiser()
        self.Loader = Loader(
            self.Core.Config.FrameworkConfigGet('POUTPUT_TEMPLATES_DIR'))
        self.mNumLinesToShow = 15
        self.CounterList = []

    def TransactionTableFromIDs(
            self,
            TransactionIDs,
            NumLinesReq=15,
            NumLinesRes=15):
        """ Draws a table of HTTP Transactions """
        # functions to get the first lines of a long string
        transactions = self.Core.DB.Transaction.GetByIDs(TransactionIDs)
        return self.TransactionTableForTransactions(transactions)

    def TransactionTableForURL(self, UseCache, URL, Method=None, Data=None):
        transaction = self.Core.Requester.GetTransaction(
            UseCache, URL, method=Method, data=Data)
        return self.TransactionTableForTransactions([transaction])

    def TransactionTableForURLList(
            self,
            UseCache,
            URLList,
            Method=None,
            Data=None):
        transactions = self.Core.Requester.GetTransactions(
            UseCache,
            URLList,
            method=Method,
            data=Data)
        return self.TransactionTableForTransactions(transactions)

    def TransactionTableForTransactions(self, Transactions):
        return self.Loader.load("transaction_table.html").generate(
            TransactionList=Transactions)

    def unicode(self, *args):
        try:
            return unicode(*args)
        except TypeError:
            return args[0]  # Input is already Unicode

# ----------------- Methods exported from plugin_helper.py ----------------- #

    def CommandTable(self, Command):
        return self.Loader.load("command_table.html").generate(Command=Command)

    def LinkList(self, LinkListName, Links):
        """
        Wrapper to allow rendering a bunch of links -without name- as resource
        links with name = link
        """
        return self.Loader.load("link_list.html").generate(
            LinkListName=LinkListName,
            Links=Links)

    def ResourceLinkList(self, ResourceListName, ResourceList):
        """
        Draws an HTML Search box for defined Vuln Search resources
        """
        return self.Loader.load("resource_link_list.html").generate(
            ResourceListName=ResourceListName,
            ResourceList=ResourceList)

    def TabbedResourceLinkList(self, ResourcesList):
        """
        ResourceList = [
            "ResourceListName", [["Name1","Resource1"],["Name2","Resource2"]]
        ]
        """
        TabData = []
        Resources = []
        for ResourceListName, ResourceList in ResourcesList:
            TabID = ResourceListName.replace(' ', '_')
            TabData.append([ResourceListName, TabID])
            Resources.append([TabID, ResourceList])
        return self.Loader.load("tabbed_resource_link_list.html").generate(
            TabData=TabData,
            Resources=Resources)

    def ListPostProcessing(self, ResourceListName, LinkList, HTMLLinkList):
        return self.Loader.load("list_post_processing.html").generate(
            ResourceListName=ResourceListName,
            LinkList=LinkList,
            HTMLLinkList=HTMLLinkList)

    def RequestLinkList(self, ResourceListName, LinkList):
        return self.Loader.load("request_link_list.html").generate(
            ResourceListName=ResourceListName,
            LinkList=LinkList)

    def VulnerabilitySearchBox(self, SearchStr):
        """
        Draws an HTML Search box for defined Vuln Search resources
        """
        VulnSearchResources = self.Core.DB.Resource.GetResources('VulnSearch')
        return self.Loader.load("vulnerability_search_box.html").generate(
            SearchStr=SearchStr,
            VulnSearchResources=VulnSearchResources)

    def SuggestedCommandBox(
            self,
            PluginOutputDir,
            CommandCategoryList,
            Header=''):
        """
        Draws HTML tabs for a list of TabName => Resource Group (i.e. how to run hydra, etc)
        """
        TitleList = []
        CommandList = []
        for item in CommandCategoryList:
            TitleList.append(item[0])
            CommandList.append(self.Core.DB.Resource.GetResources(item[1]))
        return self.Loader.load("suggested_command_box.html").generate(
            Header=Header,
            TitleList=TitleList,
            CommandList=CommandList)  # TODO: Fix up the plugin

    def CommandDump(
            self,
            Name,
            CommandIntro,
            ModifiedCommand,
            RelativeFilePath,
            OutputIntro,
            TimeStr):
        AbsPath = self.Core.PluginHandler.RetrieveAbsPath(RelativeFilePath)
        OutputLines = open(AbsPath, "r").readlines()
        longOutput = (len(OutputLines) > self.mNumLinesToShow)
        if (len(OutputLines) > self.mNumLinesToShow):
            OutputLines = ''.join(OutputLines[0:self.mNumLinesToShow])
        else:
            OutputLines = ''.join(OutputLines)
        table_vars = {
            "Name": Name,
            "CommandIntro": CommandIntro,
            "ModifiedCommand": ModifiedCommand,
            "FilePath": RelativeFilePath,
            "OutputIntro":  OutputIntro,
            "OutputLines": OutputLines,
            "TimeStr": TimeStr,
            "mNumLinesToShow": self.mNumLinesToShow,
            "longOutput": longOutput
        }
        return self.Loader.load("command_dump.html").generate(**table_vars)

    def URLsFromStr(self, TimeStr, VisitURLs, URLList, NumFound):
        html_content = self.Loader.load("urls_from_str.html").generate(
            TimeStr=TimeStr,
            VisitURLs=VisitURLs,
            NumURLs=len(URLList),
            NumFound=NumFound)
        if URLList:
            html_content += self.LinkList("URLs Scraped", URLList)
        return html_content

    def Robots(
            self,
            RobotsFound,
            NumLines,
            NumAllow,
            NumDisallow,
            NumSitemap,
            SavePath,
            EntriesList):
        vars = {
            "robots_found": RobotsFound,
            "num_lines": NumLines,
            "num_allow": NumAllow,
            "num_disallow": NumDisallow,
            "num_sitemap": NumSitemap,
            "save_path": SavePath,
        }
        TestResult = self.Loader.load("robots.html").generate(**vars)
        # robots.txt contains some entries, show browsable list! :)
        if NumDisallow > 0 or NumAllow > 0 or NumSitemap > 0:
            for Display, Links in EntriesList:
                if Links:  # Filters empty lists
                    TestResult += self.ResourceLinkList(Display, Links)
        return TestResult

    def HtmlString(self, String):
        return(String)

# ---------------------- Grep Plugin Outputs -------------------- #
    def ResponseBodyMatches(self, ResponseRegexpName):
        RegexpName, GrepOutputs, TransactionIDS, match_percent = self.Core.DB.Transaction.\
            SearchByRegexName(ResponseRegexpName, stats=True)
        variables = {
            "name": RegexpName.replace("RESPONSE_REGEXP_FOR_", "").replace(
                '_', ' '),
            "matches": GrepOutputs,
            "transaction_ids": TransactionIDS,
            "match_percent": match_percent
        }
        return self.Loader.load("response_matches.html").generate(**variables)

    def ResponseHeaderMatches(self, HeaderRegexpName):
        return self.ResearchHeaders(HeaderRegexpName)[0]

    def ResearchHeaders(self, RegexName):
        regex_name, grep_outputs, transaction_ids, match_percent = self.Core.DB.Transaction.\
            SearchByRegexName(RegexName, stats=True)
        # [[unique_matches, matched_transactions, matched_percentage]]
        return [self.Loader.load("header_searches.html").generate(
            match_percent=match_percent,
            matches=grep_outputs,
            transaction_ids=transaction_ids), grep_outputs]

    def FingerprintData(self):
        HeaderTable, matches = self.ResearchHeaders('HEADERS_FOR_FINGERPRINT')
        for item in matches:
            # Add Vulnerability search boxes after table
            HeaderTable += self.VulnerabilitySearchBox(item[1])
        return HeaderTable

    def TopTransactionsBySpeed(self, Order):
        transactions = self.Core.DB.Transaction.GetTopTransactionsBySpeed(Order)
        return self.TransactionTableForTransactions(transactions)

    def CookieAttributeAnalysis(self, CookieValueList, Header2TransacDict):
        vars = {
            "Cookies": [{
                "Name": Cookie.split('=')[0],
                "Link":  Header2TransacDict[self.Core.Config.Get('HEADERS_FOR_COOKIES').lower() + Cookie],
                "Attribs": Cookie.replace(Cookie.split('=')[0] + "=", "").replace("; ", ";").split(";"),
            } for Cookie in CookieValueList],
        }
        Table = self.Core.Reporter.Render.CreateTable({'class': 'report_intro'})
        SetCookie = self.Core.Config.Get('HEADERS_FOR_COOKIES').lower()
        PossibleCookieAttributes = self.Core.Config.Get(
            'COOKIE_ATTRIBUTES').split(',')
        for Cookie in CookieValueList:
                CookieName = Cookie.split('=')[0]
                CookieLink = self.Core.Reporter.Render.DrawButtonLink(cgi.escape( CookieName ), Header2TransacDict[SetCookie + Cookie] )
                CookieAttribs = Cookie.replace(CookieName + "=", "").replace("; ", ";" ).split( ";" )
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
