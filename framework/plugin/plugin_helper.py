#!/usr/bin/env python
'''
This module contains helper functions to make plugins simpler to read and write, centralising common functionality easy to reuse
'''
import os
import re
import cgi
import logging

from collections import defaultdict
from tornado.template import Template
from framework.dependency_management.dependency_resolver import BaseComponent

from framework.lib.exceptions import FrameworkAbortException, \
    PluginAbortException
from framework.lib.general import *
from framework.utils import FileOperations

PLUGIN_OUTPUT = {"type": None, "output": None}  # This will be json encoded and stored in db as string


class PluginHelper(BaseComponent):
    COMPONENT_NAME = "plugin_helper"

    mNumLinesToShow = 25

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.target = self.get_component("target")
        self.url_manager = self.get_component("url_manager")
        self.plugin_handler = self.get_component("plugin_handler")
        self.reporter = self.get_component("reporter")
        self.requester = self.get_component("requester")
        self.shell = self.get_component("shell")
        self.timer = self.get_component("timer")
        # Compile regular expressions only once on init:
        self.RobotsAllowRegexp = re.compile("Allow: ([^\n  #]+)")
        self.RobotsDisallowRegexp = re.compile("Disallow: ([^\n #]+)")
        self.RobotsSiteMap = re.compile("Sitemap: ([^\n #]+)")

    def MultipleReplace(self, Text, ReplaceDict):  # This redundant method is here so that plugins can use it
        return MultipleReplace(Text, ReplaceDict)

    def CommandTable(self, Command):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "CommandTable"
        plugin_output["output"] = {"Command": Command}
        return ([plugin_output])

    def LinkList(self, LinkListName, Links):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "LinkList"
        plugin_output["output"] = {"LinkListName": LinkListName, "Links": Links}
        return ([plugin_output])

    def ResourceLinkList(self, ResourceListName, ResourceList):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "ResourceLinkList"
        plugin_output["output"] = {"ResourceListName": ResourceListName, "ResourceList": ResourceList}
        return ([plugin_output])

    def TabbedResourceLinkList(self, ResourcesList):
        # ResourceList = ["ResourceListName":[["Name1","Resource1"],["Name2","Resource2"]]]
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "TabbedResourceLinkList"
        plugin_output["output"] = {"ResourcesList": ResourcesList}
        return ([plugin_output])

    def ListPostProcessing(self, ResourceListName, LinkList, HTMLLinkList):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "ListPostProcessing"
        plugin_output["output"] = {"ResourceListName": ResourceListName, "LinkList": LinkList,
                                   "HTMLLinkList": HTMLLinkList}
        return ([plugin_output])

    def RequestLinkList(self, ResourceListName, ResourceList, PluginInfo):
        # for Name, Resource in Core.Config.GetResources('PassiveRobotsAnalysisHTTPRequests'):
        LinkList = []
        for Name, Resource in ResourceList:
            Chunks = Resource.split('###POST###')
            URL = Chunks[0]
            POST = None
            Method = 'GET'
            if len(Chunks) > 1:  # POST
                Method = 'POST'
                POST = Chunks[1]
                Transaction = self.requester.GetTransaction(True, URL, Method, POST)
            if Transaction.Found:
                RawHTML = Transaction.GetRawResponseBody()
                FilteredHTML = self.reporter.sanitize_html(RawHTML)
                NotSandboxedPath = self.plugin_handler.DumpOutputFile("NOT_SANDBOXED_" + Name + ".html",
                                                                      FilteredHTML, PluginInfo)
                logging.info("File: " + "NOT_SANDBOXED_" + Name + ".html" + " saved to: " + NotSandboxedPath)
                iframe_template = Template("""
                        <iframe src="{{ NotSandboxedPath }}" sandbox="" security="restricted"  frameborder = '0' style = "overflow-y:auto; overflow-x:hidden;width:100%;height:100%;" >
                        Your browser does not support iframes
                        </iframe>
                        """)
                iframe = iframe_template.generate(NotSandboxedPath=NotSandboxedPath.split('/')[-1])
                SandboxedPath = self.plugin_handler.DumpOutputFile("SANDBOXED_" + Name + ".html", iframe,
                                                                   PluginInfo)
                logging.info("File: " + "SANDBOXED_" + Name + ".html" + " saved to: " + SandboxedPath)
                LinkList.append(( Name, SandboxedPath ))
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "RequestLinkList"
        plugin_output["output"] = {"ResourceListName": ResourceListName, "LinkList": LinkList}
        return ([plugin_output])

    def VulnerabilitySearchBox(self, SearchStr):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "VulnerabilitySearchBox"
        plugin_output["output"] = {"SearchStr": SearchStr}
        return ([plugin_output])

    def SuggestedCommandBox(self, PluginInfo, CommandCategoryList, Header=''):
        plugin_output = dict(PLUGIN_OUTPUT)
        PluginOutputDir = self.InitPluginOutputDir(PluginInfo)
        plugin_output["type"] = "SuggestedCommandBox"
        plugin_output["output"] = {"PluginOutputDir": PluginOutputDir, "CommandCategoryList": CommandCategoryList,
                                   "Header": Header}
        return ([plugin_output])

    def SetConfigPluginOutputDir(self, PluginInfo):
        PluginOutputDir = self.plugin_handler.GetPluginOutputDir(PluginInfo)
        self.target.SetPath('plugin_output_dir', os.getcwd() + '/' + PluginOutputDir)  # FULL output path for plugins to use
        self.shell.RefreshReplacements()  # Get dynamic replacement, i.e. plugin-specific output directory
        return PluginOutputDir

    def InitPluginOutputDir(self, PluginInfo):
        PluginOutputDir = self.SetConfigPluginOutputDir(PluginInfo)
        FileOperations.create_missing_dirs(PluginOutputDir)  # Create output dir so that scripts can cd to it :)
        return PluginOutputDir

    def RunCommand(self, Command, PluginInfo, PluginOutputDir):
        FrameworkAbort = PluginAbort = False
        if not PluginOutputDir:
            PluginOutputDir = self.InitPluginOutputDir(PluginInfo)
        self.timer.start_timer('FormatCommandAndOutput')
        ModifiedCommand = self.shell.GetModifiedShellCommand(Command, PluginOutputDir)
        try:
            RawOutput = self.shell.shell_exec_monitor(ModifiedCommand, PluginInfo)
        except PluginAbortException, PartialOutput:
            RawOutput = str(PartialOutput.parameter)  # Save Partial Output
            PluginAbort = True
        except FrameworkAbortException, PartialOutput:
            RawOutput = str(PartialOutput.parameter)  # Save Partial Output
            FrameworkAbort = True

        TimeStr = self.timer.get_elapsed_time_as_str('FormatCommandAndOutput')
        logging.info("Time=" + TimeStr)
        return [ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir]

    def GetCommandOutputFileNameAndExtension(self, InputName):
        OutputName = InputName
        OutputExtension = "txt"
        if InputName.split('.')[-1] in ['html']:
            OutputName = InputName[0:-5]
            OutputExtension = "html"
        return [OutputName, OutputExtension]


    def EscapeSnippet(self, Snippet, Extension):
        if Extension == "html":  # HTML
            return str(Snippet)
        return cgi.escape(str(Snippet))  # Escape snippet to avoid breaking HTML


    def CommandDump(self, CommandIntro, OutputIntro, ResourceList, PluginInfo, PreviousOutput):
        output_list = []
        PluginOutputDir = self.InitPluginOutputDir(PluginInfo)
        for Name, Command in ResourceList:
            dump_file_name = os.path.splitext(Name)[0] + ".txt"  # Add txt extension to avoid wrong mimetypes
            plugin_output = dict(PLUGIN_OUTPUT)
            ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir = self.RunCommand(Command,
                                                                                                                PluginInfo,
                                                                                                                PluginOutputDir)
            plugin_output["type"] = "CommandDump"
            plugin_output["output"] = {
                "Name": self.GetCommandOutputFileNameAndExtension(Name)[0],
                "CommandIntro": CommandIntro,
                "ModifiedCommand": ModifiedCommand,
                "RelativeFilePath": self.plugin_handler.DumpOutputFile(dump_file_name, RawOutput, PluginInfo,
                                                                       RelativePath=True),
                "OutputIntro": OutputIntro,
                "TimeStr": TimeStr
            }
            plugin_output = [plugin_output]
            if Name == self.config.FrameworkConfigGet('EXTRACT_URLS_RESERVED_RESOURCE_NAME'):  # This command returns URLs for processing
                #  The plugin_output output dict will be remade if the resource is of this type
                plugin_output = self.LogURLsFromStr(RawOutput)
            # TODO: Look below to handle streaming report
            # if self.config.Get( 'UPDATE_REPORT_AFTER_EACH_COMMAND' ) == 'Yes':
            # self.reporter.SavePluginReport( Content, PluginInfo ) # Keep updating the report after each command/scanner runs
            if PluginAbort:  # Pass partial output to external handler:
                raise PluginAbortException(PreviousOutput + plugin_output)
            if FrameworkAbort:
                raise FrameworkAbortException(PreviousOutput + plugin_output)
            output_list += plugin_output
        return (output_list)


    def LogURLsFromStr(self, RawOutput):
        plugin_output = dict(PLUGIN_OUTPUT)
        self.timer.start_timer('LogURLsFromStr')
        URLList = self.url_manager.ImportURLs(RawOutput.strip().split("\n"))  # Extract and classify URLs and store in DB
        NumFound = 0
        VisitURLs = False
        if True:  # TODO: Whether or not active testing will depend on the user profile ;). Have cool ideas for profile names
            VisitURLs = True
            for Transaction in self.requester.GetTransactions(True, self.url_manager.GetURLsToVisit()):  # Visit all URLs if not in Cache
                if Transaction is not None and Transaction.Found:
                    NumFound += 1
        TimeStr = self.timer.get_elapsed_time_as_str('LogURLsFromStr')
        logging.info("Spider/URL scaper time=" + TimeStr)
        plugin_output["type"] = "URLsFromStr"
        plugin_output["output"] = {"TimeStr": TimeStr, "VisitURLs": VisitURLs, "URLList": URLList, "NumFound": NumFound}
        return ([plugin_output])

    def DumpFile(self, Filename, Contents, PluginInfo, LinkName=''):
        save_path = self.plugin_handler.DumpOutputFile(Filename, Contents, PluginInfo)
        if not LinkName:
            LinkName = save_path
        logging.info("File: " + Filename + " saved to: " + save_path)
        template = Template("""
                            <a href="{{ Link }}" target="_blank">
                                    {{ LinkName }}
                            </a>
                    """)

        return [save_path, template.generate(LinkName=LinkName, Link="../../../" + save_path)]


    def DumpFileGetLink(self, Filename, Contents, PluginInfo, LinkName=''):
        return self.DumpFile(Filename, Contents, PluginInfo, LinkName)[1]


    def AnalyseRobotsEntries(self, Contents):  # Find the entries of each kind and count them
        num_lines = len(Contents.split("\n"))  # Total number of robots.txt entries
        AllowedEntries = list(set(self.RobotsAllowRegexp.findall(Contents)))  # list(set()) is to avoid repeated entries
        num_allow = len(AllowedEntries)  # Number of lines that start with "Allow:"
        DisallowedEntries = list(set(self.RobotsDisallowRegexp.findall(Contents)))
        num_disallow = len(DisallowedEntries)  # Number of lines that start with "Disallow:"
        SitemapEntries = list(set(self.RobotsSiteMap.findall(Contents)))
        num_sitemap = len(SitemapEntries)  # Number of lines that start with "Sitemap:"
        RobotsFound = True
        if 0 == num_allow and 0 == num_disallow and 0 == num_sitemap:
            RobotsFound = False
            return [num_lines, AllowedEntries, num_allow, DisallowedEntries, num_disallow, SitemapEntries, num_sitemap,
                    RobotsFound]


    def ProcessRobots(self, PluginInfo, Contents, LinkStart, LinkEnd, Filename='robots.txt'):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "Robots"
        num_lines, AllowedEntries, num_allow, DisallowedEntries, num_disallow, SitemapEntries, num_sitemap, NotStr = self.AnalyseRobotsEntries(
            Contents)
        SavePath = self.plugin_handler.DumpOutputFile(Filename, Contents, PluginInfo, True)
        TopURL = self.target.Get('TOP_URL')
        EntriesList = []
        if num_disallow > 0 or num_allow > 0 or num_sitemap > 0:  # robots.txt contains some entries, show browsable list! :)
            self.url_manager.AddURLsStart()
            for Display, Entries in [['Disallowed Entries', DisallowedEntries], ['Allowed Entries', AllowedEntries],
                                     ['Sitemap Entries', SitemapEntries]]:
                Links = []  # Initialise category-specific link list
                for Entry in Entries:
                    if 'Sitemap Entries' == Display:
                        URL = Entry
                        self.url_manager.AddURL(URL)  # Store real links in the DB
                        Links.append([Entry, Entry])  # Show link in defined format (passive/semi_passive)
                    else:
                        URL = TopURL + Entry
                        self.url_manager.AddURL(URL)  # Store real links in the DB
                        Links.append(
                            [Entry, LinkStart + Entry + LinkEnd])  # Show link in defined format (passive/semi_passive)
                EntriesList.append(( Display, Links ))
                NumAddedURLs = self.url_manager.AddURLsEnd()
                plugin_output["output"] = {"NotStr": NotStr,
                                           "NumLines": num_lines,
                                           "NumAllow": num_allow,
                                           "NumDisallow": num_disallow,
                                           "NumSitemap": num_sitemap,
                                           "SavePath": SavePath,
                                           "NumAddedURLs": NumAddedURLs,
                                           "EntriesList": EntriesList
                }
                return ([plugin_output])

    def TransactionTable(self, transactions_list):
        # Store transaction ids in the output, so that reporter can fetch transactions from db
        trans_ids = []
        for transaction in transactions_list:
            trans_ids.append(transaction.GetID())
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "TransactionTableFromIDs"
        plugin_output["output"] = {"TransactionIDs": trans_ids}
        return ([plugin_output])

    def TransactionTableForURLList(
            self,
            UseCache,
            URLList,
            Method=None,
            Data=None):
        # Have to make sure that those urls are visited ;), so we
        # perform get transactions but don't save the transaction ids etc..
        self.requester.GetTransactions(UseCache, URLList, Method, Data)
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "TransactionTableForURLList"
        plugin_output["output"] = {"UseCache": UseCache, "URLList": URLList, "Method": Method, "Data": Data}
        return ([plugin_output])

    def TransactionTableForURL(
            self,
            UseCache,
            URL,
            Method=None,
            Data=None):
        # Have to make sure that those urls are visited ;),
        # so we perform get transactions but don't save the transaction ids
        self.requester.GetTransaction(
            UseCache,
            URL,
            method=Method,
            data=Data)
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "TransactionTableForURL"
        plugin_output["output"] = {
            "UseCache": UseCache,
            "URL": URL,
            "Method": Method,
            "Data": Data
        }
        return ([plugin_output])

    def CreateMatchTables(self, Num):
        TableList = []
        for x in range(0, Num):
            TableList.append(self.CreateMatchTable())
        return TableList

    def HtmlString(self, html_string):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "HtmlString"
        plugin_output["output"] = {"String": html_string}
        return ([plugin_output])

    def FindResponseHeaderMatchesForRegexpName(self, HeaderRegexpName):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "ResponseHeaderMatches"
        plugin_output["output"] = {"HeaderRegexpName": HeaderRegexpName}
        return ([plugin_output])

    def FindResponseHeaderMatchesForRegexpNames(self, HeaderRegexpNamesList):
        Results = []
        for HeaderRegexpName in HeaderRegexpNamesList:
            Results += self.FindResponseHeaderMatchesForRegexpName(HeaderRegexpName)
        return Results

    def FindResponseBodyMatchesForRegexpName(self, ResponseRegexpName):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "ResponseBodyMatches"
        plugin_output["output"] = {"ResponseRegexpName": ResponseRegexpName}
        return ([plugin_output])

    def FindResponseBodyMatchesForRegexpNames(self, ResponseRegexpNamesList):
        Results = []
        for ResponseRegexpName in ResponseRegexpNamesList:
            Results += self.FindResponseBodyMatchesForRegexpName(ResponseRegexpName)
        return Results

    def ResearchFingerprintInlog(self):
        # log("Researching Fingerprint in Log ..")
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "FingerprintData"
        plugin_output["output"] = {}
        return ([plugin_output])

    def FindTopTransactionsBySpeed(self, Order="Desc"):
        plugin_output = dict(PLUGIN_OUTPUT)
        plugin_output["type"] = "TopTransactionsBySpeed"
        plugin_output["output"] = {"Order": Order}
        return ([plugin_output])
