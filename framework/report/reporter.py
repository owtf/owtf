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
from jinja2 import Template
from jinja2 import Environment, PackageLoader
from framework.lib.general import *
from framework.report.html import renderer
from framework.report.html.filter import sanitiser
from framework.report import summary

class Reporter:
    def __init__(self, CoreObj):
        self.Core = CoreObj  # Keep Reference to Core Object
        self.Init = False
        self.Render = renderer.HTMLRenderer(self.Core)
        self.Summary = summary.Summary(self.Core)
        self.Sanitiser = sanitiser.HTMLSanitiser()
        self.PluginDivIds = {}
        self.CounterList = []
        # prepare the environment of html templates
        Loader = PackageLoader('framework.report', 'templates')
        self.Template_env = Environment(loader=Loader)
        # make shortcuts to config functions
        self.CCG = self.Core.Config.Get
        self.CCGAPP = self.Core.Config.GetAsPartialPath

    def GetPluginDelim(self):
        return summary.PLUGIN_DELIM

    def CopyAccessoryFiles(self):
        TargetOutputDir = self.CCG('OUTPUT_PATH')
        FrameworkDir = self.CCG('FRAMEWORK_DIR')
        log("Copying report images ..")
        self.Core.Shell.shell_exec("cp -r " + FrameworkDir + "/images/ " + TargetOutputDir)
        log("Copying report includes (stylesheet + javascript files)..")
        self.Core.Shell.shell_exec("cp -r " + FrameworkDir + "/includes/ " + TargetOutputDir)

    def GetPluginDivId(self, Plugin):
        # "Compression" attempt while keeping uniqueness:
        # First letter from plugin type is enough to make plugin div ids unique and predictable
        #return MultipleReplace(Code, { 'OWASP' : 'O', 'OWTF' : 'F', '-' : '', '0' : '' })+PluginType[0]
        return self.GetPluginDelim().join([ Plugin['Group'], Plugin['Type'], Plugin['Code'] ]) # Need this info for fast filtering in JS

    def DrawCommand(self, Command):
        #cgi.escape(MultipleReplace(ModifiedCommand, self.Core.Config.GetReplacementDict()))
        return cgi.escape(Command)#.replace(';', '<br />') -> Sometimes ";" encountered in UA, cannot do this and it is not as helpful anyway

    def DrawTransacLinksStr(self, PathList, ForPlugin = False):
        URL, TransacPath, ReqPath, ResHeadersPath, ResBodyPath = PathList
        template = Template("""
            <!-- Start Transactions Links -->
            <a href="{{ Transaction_URL }}" class="label label-info" target="_blank">
                Site
            </a>
            <a href="{{ Base_Path }}{{ Transaction_Path }}" class="label" target="_blank">
                F
            </a>
            <a href="{{ Base_Path }}{{ Request_Path }}" class="label" target="_blank">
                R
            </a>
            <a href="{{ Base_Path }}{{ Resource_Headers_Path }}" class="label" target="_blank">
                H
            </a>
            <a href="{{ Base_Path }}{{ Resource_Body_Path }}" class="label" target="_blank">
                B
            </a>
            <!-- End Transactions Links -->
                        """)
        vars = {
                "Transaction_URL": URL,
                "Transaction_Path":  TransacPath,
                "Request_Path": ReqPath,
                "Resource_Headers_Path": ResHeadersPath ,
                "Resource_Body_Path": ResBodyPath,
                "Base_Path": "../" if not ForPlugin else "../../../../"
            }
        return template.render(vars)

    def DrawTransacLinksForID(self, ID, ForPlugin=False):
        # Returns the URL and Transaction Paths for a given Transaction ID
        PathList = self.Core.DB.Transaction.GetTransactionPathsForID(ID)

        CleanPathList = [PathList[0]]  # Leave URL unmodified
        if ForPlugin:
            for Path in PathList[1:]:  # Skip URL, process rest of items in list
                CleanPathList.append('../../../' + Path)
        else:
            CleanPathList = PathList
        return self.DrawTransacLinksStr(CleanPathList, ForPlugin)

    def SavePluginReport(self, HTMLtext, Plugin):
        save_dir = self.Core.PluginHandler.GetPluginOutputDir(Plugin)
        if HTMLtext == None:
            HTMLtext = cprint(
                              "PLUGIN BUG!!: on: " + Plugin["Type"].strip() \
                              + "/" + Plugin["File"].strip() \
                              + " no content returned"
                              )

        PluginReportPath = save_dir + "report.html"
        self.Core.CreateMissingDirs(save_dir)
        with codecs.open(PluginReportPath, 'w',"utf-8") as file: # 'w' is important to overwrite the partial report, necesary for scanners
            Plugin['RunTime'] = self.Core.Timer.GetElapsedTimeAsStr('Plugin')
            Plugin['End'] = self.Core.Timer.GetEndDateTimeAsStr('Plugin')
            plugin_report_template = self.Template_env.get_template('plugin_report.html')
            plugin_report_vars = {
                    "DivId": self.GetPluginDivId(Plugin),
                    "SAVE_DIR": save_dir, 
                    "REVIEW_OFFSET" : self.CCG('REVIEW_OFFSET'),
                    "ReportID": "i"+ self.CCG('HOST_IP').replace(".","_") \
                            + "p" + self.CCG('PORT_NUMBER'),
                    "NextHTMLID": self.Core.DB.GetNextHTMLID(),
                    "Plugin": Plugin,
                    "HTMLtext": unicode(HTMLtext, "utf-8") if HTMLtext.__class__ is not unicode else HTMLtext,
                    "PluginTypes": self.Core.Config.Plugin.GetAllGroups(),
                    "WebPluginTypes": self.Core.Config.Plugin.GetTypesForGroup('web'),
                    "AuxPluginsTypes": self.Core.Config.Plugin.GetTypesForGroup('aux'),
                    "WebTestGroups":self.Core.Config.Plugin.GetWebTestGroups(),
                    }
            file.write(plugin_report_template.render(plugin_report_vars).encode('ascii', 'ignore'))
            #print "Plugin="+str(Plugin)
        self.Core.DB.PluginRegister.Add(Plugin, PluginReportPath, self.Core.Config.GetTarget())
        #self.RegisterPartialReport(PluginReportPath) # Partial report saved ok, register partial report in register file for grouping later
        
        # Provide a full partial report at the end of each plugin
        #self.ReportFinish()

    def DrawHTTPTransactionTable(self, TransactionList, NumLinesReq=15, NumLinesRes=15):
        """ Draws a table of HTTP Transactions """
        # functions to get the first lines of a long string
        GetFirstLines = lambda s,n: "\n".join(s.split("\n")[:n]) + " ... " if n <= len(s) else s
        http_transaction_table_template = self.Template_env.get_template('http_transaction_table.html')
        http_transaction_table_vars = { 
            "NumLinesReq":  NumLinesReq,
            "NumLinesRes": NumLinesRes,
            "TransactionList":[
                {
                    "HTMLLink": Transaction.HTMLLinkToID.replace('@@@PLACE_HOLDER@@@', "See Transaction " + Transaction.ID),
                    "TimeHuman": Transaction.TimeHuman,
                    "LinksForID": self.DrawTransacLinksForID(Transaction.ID),
                    "RawRequest": self.unicode(GetFirstLines(Transaction.GetRawRequest(),25), "utf-8"),
                    "RawResponse": self.unicode(GetFirstLines(Transaction.GetRawResponse(),25), "utf-8"),
                } for Transaction in TransactionList
                    ]
            }
        return http_transaction_table_template.render(http_transaction_table_vars)

    def unicode(self, *args):
        try:
            return unicode(*args)
        except TypeError:
            return args[0]  # Input is already Unicode

    def GetRegisteredWebPlugins(self, ReportType):
        """ Web Plugins go in OWASP Testing Guide order """
        TestGroups = []
        for TestGroup in self.Core.Config.Plugin.GetWebTestGroups():  #Follow defined web test group order, NOT execution order
            RegisteredPlugins = self.Core.DB.PluginRegister.Search(
                                                {
                                                 'Code': TestGroup['Code'],
                                                 'Target': self.Core.Config.GetTarget()
                                                 })
            if not RegisteredPlugins:
                continue  # The plugin has not been registered yet
            RegisteredPluginList = []
            for Match in RegisteredPlugins:
                Match['Label'] = Match['Type'] # For url plugins the Label is a display of the plugin type (passive, semi_passive, etc)
                RegisteredPluginList.append(Match)
            TestGroups.append(
                                {
                                'TestGroupInfo':  TestGroup,
                                 'RegisteredPlugins' : RegisteredPluginList
                                 }
                            )
        return TestGroups

    def GetRegisteredNetPlugins(self, ReportType):
        """ netPlugins go in OWASP Testing Guide order """
        TestGroups = []
        for TestGroup in self.Core.Config.Plugin.GetNetTestGroups():  #Follow defined web test group order, NOT execution order
            RegisteredPlugins = self.Core.DB.PluginRegister.Search({ 'Code' : TestGroup['Code'], 'Target' : self.Core.Config.GetTarget() })
            if not RegisteredPlugins:
                continue  # The plugin has not been registered yet
            RegisteredPluginList = []
            for Match in RegisteredPlugins:
                Match['Label'] = Match['Type']  # For url plugins the Label is a display of the plugin type (passive, semi_passive, etc)
                RegisteredPluginList.append(Match)

            TestGroups.append(
                                {
                                    'TestGroupInfo': TestGroup,
                                    'RegisteredPlugins': RegisteredPluginList
                                }
                           )
        return TestGroups

    def GetRegisteredAuxPlugins(self, ReportType): 
        """ Web Plugins go in OWASP Testing Guide order  """
        TestGroups = []
        for PluginType in self.Core.Config.Plugin.GetTypesForGroup('aux'):  # Report aux plugins in alphabetical order
            RegisteredPlugins = self.Core.DB.PluginRegister.Search({ 'Type' : PluginType, 'Target' : 'aux' }) # Aux plugins have an aux target
            if not RegisteredPlugins:
                continue  # The plugin has not been registered yet
            RegisteredPluginList = []
            for Match in RegisteredPlugins:
                Match['Label'] = Match['Args']  # For aux plugins the Label is a display of the arguments passed
                RegisteredPluginList.append(Match)

            TestGroups.append({
                                'TestGroupInfo': { "PluginType":PluginType },
                                'RegisteredPlugins' : RegisteredPluginList
                                 }
                            )
        return TestGroups

    def GetTestGroups(self, ReportType):
        if ReportType == 'URL':
            return self.GetRegisteredWebPlugins(ReportType)
        elif ReportType == 'AUX':
            return self.GetRegisteredAuxPlugins(ReportType)
        elif ReportType == 'NET':
            return self.GetRegisteredNetPlugins(ReportType)

    def ReportFinish(self, Target,registered_plugins):
        """ Group all partial reports (whether done before or now)
        into the final report """
        #Target = self.Core.Config.GetTarget()
        self.Core.PluginHandler.SwitchToTarget(Target) 
        #NumPluginsForTarget = self.Core.DB.PluginRegister.NumPluginsForTarget(Target)
        #if not NumPluginsForTarget > 0:
        #    log("No plugins completed for target, cannot generate report")
        #    return None  # Must abort here, before report is generated
        #ReportStart -- Wipe report
        self.CounterList = []
        if not self.Init:
            # The report is re-generated several times, this ensures images,
            # style sheets, etc are only copied once at the start
            self.CopyAccessoryFiles()
            self.Init = True
        with codecs.open(self.CCG('HTML_DETAILED_REPORT_PATH'), 'w',"utf-8") as file:
            report_template = self.Template_env.get_template('report.html')
            report_vars = {
                "ReportID": "i"+ self.CCG('HOST_IP').replace(".","_") \
                            + "p" + self.CCG('PORT_NUMBER'),
                "ReportType" :  self.CCG('REPORT_TYPE'),
                "Title" :  self.CCG('REPORT_TYPE') + " Report",
                "Seed": self.Core.GetSeed(),
                "Version": self.CCG('VERSION'),
                "Release": self.CCG('RELEASE'),
                "HTML_REPORT": self.CCG('HTML_REPORT'),
                "TargetLink": self.CCG('TARGET_URL'),
                "HostIP":  self.CCG('HOST_IP'),
                "AlternativeIPs": self.CCG('ALTERNATIVE_IPS'),
                "PortNumber":  self.CCG('PORT_NUMBER'),
                "RUN_DB": self.Core.DB.GetData('RUN_DB'),
                "PluginTypes": self.Core.Config.Plugin.GetAllGroups(),
                "WebPluginTypes": self.Core.Config.Plugin.GetTypesForGroup('web'),
                "AuxPluginsTypes": self.Core.Config.Plugin.GetTypesForGroup('aux'),
                "WebTestGroups":self.Core.Config.Plugin.GetWebTestGroups(),
                "Globals": {
                        "AllPlugins":[
                            self.GetPluginDivId(Match)
                            for TestGroup in self.GetTestGroups(self.CCG('REPORT_TYPE')) 
                            for Match in TestGroup['RegisteredPlugins']
                            ],
                        "AllCodes": list(set([
                            Match['Code'] #eliminate repetitions,
                             for TestGroup in self.GetTestGroups(self.CCG('REPORT_TYPE')) 
                             for Match in TestGroup['RegisteredPlugins']
                            ])),
                        },
                        "TestGroups": [
                            {
                            "TestGroupInfo": TestGroup['TestGroupInfo'],
                            "Matches" : [
                                {
                                "PluginId": self.GetPluginDivId(Match),
                                "PluginName": Match["Label"],
                                "PluginContent": open(Match['Path']).read(),
                                }
                                for Match in TestGroup['RegisteredPlugins']
                                ],
                            }
                            for TestGroup in self.GetTestGroups(self.CCG('REPORT_TYPE'))
                            ],
                "REVIEW_OFFSET" : self.CCG('REVIEW_OFFSET'),

                    }
            # Closing HTML Report
            file.write(report_template.render(report_vars))
            log("Report written to: " + self.CCG('HTML_DETAILED_REPORT_PATH'))
            # Register report
            params_list = [ 
                            'REVIEW_OFFSET', 
                            'SUMMARY_HOST_IP', 
                            'SUMMARY_PORT_NUMBER', 
                            'HTML_DETAILED_REPORT_PATH', 
                            'REPORT_TYPE' 
                        ]
            requested_params_list = self.Core.Config.GetAsList(params_list)
            self.Core.DB.ReportRegister.Add(requested_params_list)
            # Build summary report
            self.Summary.ReportFinish()
