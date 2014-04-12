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
        with codecs.open(self.CCG('HTML_DETAILED_REPORT_PATH'), 'w',"utf-8") as file:
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

#----------------------------------- Methods exported from plugin_helper.py ---------------------------------

    def CommandTable( self, Command ):
        template = Template ( """
                        <table class="table table-bordered"> 
                                <thead>
                                <tr>
                                        <th> Analysis Command </th>
                                </tr>
                        </thead>
                        <tbody>
                                <tr> 
                                        <td>
                                                {{ Command|e }}
                                        </td>
                                </tr>
                        </tbody>
                        </table>
                        """ )
        vars = {
                                         "Command": Command,
                                        }
        return template.render( vars )

    def LinkList( self, LinkListName, Links ): # Wrapper to allow rendering a bunch of links -without name- as resource links with name = link
        template = Template( """
        <div class="well well-small">
                {{ LinkListName }}: 

                <ul class="icons-ul">
                {% for Link in Links %}
                        <li> 
                                <i class="icon-li icon-chevron-sign-right"></i>
                                <a href="{{ Link|e }}" class="button" target="_blank">
                                
                                        <span> {{ Link }} </span> 
                                        </a> 
                                </li>
                {% endfor %}
                </ul>
        </div>
        """ )
        return template.render( LinkListName = LinkListName, Links = Links )

    def ResourceLinkList( self, ResourceListName, ResourceList ): # Draws an HTML Search box for defined Vuln Search resources
        template = Template( """
        <div class="well well-small">
                {{ ResourceListName }} ( <a href="#" onclick="$(this).parent().find('a[target]').trigger('click');"> Open all </a> ): 

                <ul class="icons-ul">
                {% for Name, Resource in ResourceList %}
                        <li> 
                                <i class="icon-li icon-chevron-sign-right"></i>
                                <a href="{{ Resource|e }}" onclick="window.open(this.href); return false;" target="_blank">
                                 {{ Name }} 
                                        </a> 
                                </li>
                {% endfor %}
                </ul>
        </div>
        """ )
        return template.render( ResourceListName = ResourceListName, ResourceList = ResourceList )

    def TabbedResourceLinkList(self, ResourcesList):
        # ResourceList = ["ResourceListName":[["Name1","Resource1"],["Name2","Resource2"]]]
        template = Template("""
            <div class="well well-small">
                <ul class="nav nav-tabs">
                {% for TabName, TabID in TabData %}
                    <li><a href="#{{ TabID }}" data-toggle="tab">{{ TabName }}</a></li>
                {% endfor %}
                </ul>
                 
                <div class="tab-content">
                {% for TabID, ResourceList in Resources %}
                 <div class="tab-pane" id="{{ TabID }}">
                     <div class="well well-small">
                     ( <a href="#" onclick="$(this).parent().find('a[target]').trigger('click');"> Open all </a> ):

                         <ul class="icons-ul">
                         {% for Name, Resource in ResourceList %}
                             <li>
                                 <i class="icon-li icon-chevron-sign-right"></i>
                                 <a href="{{ Resource|e }}" onclick="window.open(this.href); return false;" target="_blank">
                                    {{ Name }}
                                 </a>
                             </li>
                         {% endfor %}
                         </ul>
                     </div>
                 </div>
                {% endfor %}
                </div>
            </div>""")
        vars = {
                "TabData": [],
                "Resources": []
               }
        for ResourceListName, Resources in ResourcesList:
            TabID = ResourceListName.replace(' ','_')
            vars["TabData"].append([ResourceListName, TabID])
            vars["Resources"].append([TabID, Resources])
        return template.render(vars)

    def ListPostProcessing( self, ResourceListName, LinkList, HTMLLinkList ):
        template = Template( """
        <div class="well well-small">
                {{ ResourceListName }}: 
         
        <ul class="icons-ul">
        {% for HTMLLink in HTMLLinkList %}
                <li><i class="icon-li icon-chevron-sign-right"></i>  {{ HTMLLink }} </li>
        {% endfor %}
        </ul>
        </div>
        """ )
        return template.render( ResourceListName = ResourceListName, LinkList = LinkList, HTMLLinkList = HTMLLinkList )

    def RequestLinkList( self, ResourceListName, LinkList ):
        template = Template( """
        <div class="well  well-small">
                {{ ResourceListName }}: 
         
                <ul class="icons-ul">
                {% for LinkName, Link in LinkList %}
                        <li><i class="icon-li icon-chevron-sign-right"></i>
                         <a href="../../../{{ Link|e }}" class="button" target="_blank">
                                                <span> {{ LinkName }} </span>
                                        </a> </li>
                {% endfor %}
                </ul>
        </div>
        """ )
        return template.render( ResourceListName = ResourceListName, LinkList = LinkList )

    def VulnerabilitySearchBox( self, SearchStr ): # Draws an HTML Search box for defined Vuln Search resources
            template = Template( """
            <table class="table table-bordered ">
                    <tr>
                            <th colspan="{{ VulnSearchResources|count }}">
                                    Search for Vulnerabilities: <input name="product" id='prod{{ ProductId }}' type="text" size="35" value='{{ SearchStr }}'>
                                    <button class="btn btn-primary" onclick="javascript:
                                                                    {% for Name, Resource in VulnSearchResources %}
                                                                            {% set js_selector = "'+GetById('prod"+ ProductId +"').value +'" %}
                                                                            {% set js_link = Resource|replace("@@@PLACE_HOLDER@@@",js_selector) %}
                                                                                    window.open('{{ js_link|replace("\n", "") -}}');
                                                                    {% endfor %}
                                                                    ">Search All</button>
                            </th>
                    </tr>
                    <tr>
                     {% for Name, Resource in VulnSearchResources %}
                            <td>  
                                    {% set js_selector = "'+GetById('prod"+ ProductId + "').value+'" %}
                                    {% set js_link = Resource|replace("@@@PLACE_HOLDER@@@",js_selector) %}
                                    <button onclick="javascript:window.open('{{ js_link|replace("\n", "") -}}') "> 
                                            {{ Name }} 
                                    </button>   
                            </td>
                     {% endfor %}
                    </tr>
            </table>
            <hr />
            """ )
            return template.render( ProductId = self.Core.DB.GetNextHTMLID() , SearchStr = SearchStr, VulnSearchResources = self.Core.DB.Resource.GetResources( 'VulnSearch' ) )

    def SuggestedCommandBox( self, PluginInfo, CommandCategoryList, Header = '' ): # Draws HTML tabs for a list of TabName => Resource Group (i.e. how to run hydra, etc)
            PluginOutputDir = self.InitPluginOutputDir( PluginInfo )
            template = Template( """
                    <hr />
                    <h4> 
                            {% if Header %}
                                    Header 
                            {% else %}
                                    Suggested potentially interesting commands
                            {% endif %}
                    </h4>
                    <ul id="tabs">
                            {% for CommandCategory in CommandCategoryList %}
                                    <li>
                                                    <a href="javascript:void(0);" id="tab_{{ CommandCategory.Tab|replace( ' ', '_' )|lower }}" target=""
                                                                    onclick="SetClassNameToElems(new Array('{{ TabIdList|join("','") }}'), '');
                                                                                     HideDivs(new Array('{{ DivIdList|join("','") }}'));
                                                                                     this.className = 'selected'; 
                                                                                     ToggleDiv('{{ CommandCategory.Tab|replace( ' ', '_' )|lower }}');" >
                                                            {{ CommandCategory.Tab }}
                                                    </a>
                                    </li>
                            {% endfor %}
                    </ul>
                    {% for CommandCategory in CommandCategoryList %}
                            <div id="{{ CommandCategory.Tab|replace( ' ', '_' )|lower }}" class="tabContent" style="display:none">
                                                                    <table class="run_log"> 
                                                                            {% for ResourceGroup in  CommandCategory.ResourceGroups %} 
                                                                             <tr> 
                                                                                    <th> {{ ResourceGroup.Name }}   </th>
                                                                            </tr>
                                                                             <tr> 
                                                                                    <td> {{ ResourceGroup.ModifiedCommand }} </td>
                                                                            </tr>
                                                                            {% endfor %}
                                                                    </table>
                                                            </div>
                    {% endfor %}


                    
            """ )

            vars = {
                                    "TabIdList": [ "tab_" + Tab.replace( ' ', '_' ).lower() for Tab, ResourceGroup in CommandCategoryList ],
                                    "DivIdList": [ Tab.replace( ' ', '_' ).lower() for Tab, ResourceGroup in CommandCategoryList ],
                                    "CommandCategoryList": [
                                                                            {
                                                                            "Tab": Tab,
                                                                            "ResourceGroups": [
                                                                                                                     {
                                                                                                                     "Name": Name,
                                                                                                                     "ModifiedCommand": self.MultipleReplace( self.Core.Shell.GetModifiedShellCommand( Resource.strip(), PluginOutputDir ), self.Core.Config.GetReplacementDict() )

                                                                                                                    } for Name, Resource in self.Core.DB.Resource.GetResources( ResourceGroup )
                                                                                                            ]

                                                                            } for Tab, ResourceGroup in CommandCategoryList

                                                                            ]

            }

            return template.render(vars)

    def TruncateOutput( self, FilePath, RawOutput, OutputLines ):
            TruncationWarningLinkToFile = self.Core.Reporter.Render.DrawButtonLink( 'Click here to see all output!', FilePath, {}, True )
            BottomNote = ''
            NewLine = "\n"
            if len( OutputLines ) > self.mNumLinesToShow: #Show first few lines of command, rest in file
                    Snippet = NewLine.join( OutputLines[0:self.mNumLinesToShow] )
                    BottomNote = "\n <br /><span class='alert alert-warning'><strong>NOTE!</strong> Output longer than " + str( self.mNumLinesToShow ) + " lines, " + TruncationWarningLinkToFile + "</div>"
            else: # Output fits in NumLinesToShow
                    Snippet = RawOutput
            return [ BottomNote, Snippet ]

    def CommandDump( self, Name, CommandIntro, ModifiedCommand, RelativeFilePath, OutputIntro, TimeStr):
    #def FormatCommandAndOutput( self, Name, CommandIntro, ModifiedCommand, FilePath, OutputIntro, OutputLines, TimeStr):
            #ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir = self.RunCommand( Command, PluginInfo, PluginOutputDir )
        table_vars = {
                        "Name": Name,
                        "CommandIntro" : CommandIntro ,
                        "ModifiedCommand": ModifiedCommand,
                        "FilePath" : RelativeFilePath,
                        "OutputIntro":  OutputIntro,
                        "OutputLines": '', # TODO: Read using the relative path
                        "TimeStr": TimeStr,
                        "mNumLinesToShow": self.mNumLinesToShow,
                }
        table_template =Template("""
            <table class="table table-bordered table-striped"> 
                            <thead>
                                    <tr>
                                            <th>
                                                    {{ CommandIntro }}
                                            </th>
                                    </tr>
                            </thead>
                            <tbody>
                                    <tr>
                                            <td>
                                                            <pre> {{ ModifiedCommand|e }} </pre>
                                            </td>
                                    </tr>
                                    <tr>
                                            <th>
                                            <a href="../{{ FilePath }}" target="_blank">{{ Name }}</a>
                                            {{ OutputIntro }} (Execution Time: {{ TimeStr }})
                                            </th>
                                    </tr>
                                    <tr>
                                            <td>
                                             <pre> {{  OutputLines|join("\n")|e }} </pre>
                                             
                                             {% if OutputLines|count >= mNumLinesToShow %}
                                      
                                             <div class='alert alert-warning'>
                                                    <strong>NOTE!</strong>
                                                    Output longer than {{ mNumLinesToShow }} lines,
                                                    <a href="../{{ FilePath }}" target="_blank">
                                            Click here to see all output!
                                            </a>
                                             </div>
                                      
                                             {% endif %}
                                            </td>
                                    </tr>
                            </tbody>
        </table>
            """)
        return table_template.render(table_vars)

    def URLsFromStr(self, TimeStr, VisitURLs, URLList, NumFound):
        Table = self.Core.Reporter.Render.CreateTable({'class' : 'commanddump'})
        Table.CreateCustomRow('<tr><th colspan="2">Spider/URL scraper</th></tr>')
        Table.CreateRow(['Time', 'URL stats'], True)
        Table.CreateRow([TimeStr, self.Core.Reporter.Render.DrawHTMLList(['Visited URLs?: '+str(VisitURLs), str(len(URLList))+' URLs scraped', str(NumFound)+' URLs found'])])
        return Table.Render()

    def Robots(self, NotStr, NumLines, NumAllow, NumDisallow, NumSitemap, SavePath, NumAddedURLs, EntriesList):
        template = Template(
                                        """
                                        <div class="alert {% if NotStr == "not" %}alert-warning{% else %}alert-success{% endif %}">
                                          robots.txt was <strong>{{ NotStr }}</strong> found.
                                          <br />
                                          <strong>{{ num_lines }} lines:</strong> {{ num_allow }} Allowed,  {{ num_disallow }} Disallowed, {{ num_sitemap }} Sitemap.
                                          <br />
                                          Saved to: {{ save_link }}
                                        </div>
                                        """
                                        )
        vars = {
                         "NotStr":  NotStr,
                         "num_lines": NumLines, 
                         "num_allow": NumAllow,
                         "num_disallow": NumDisallow,
                         "num_sitemap": NumSitemap,
                         "save_link": self.Core.Reporter.Render.DrawButtonLink( SavePath, SavePath, {}, True ),
                }
        TestResult =  template.render(vars)
        if num_disallow > 0 or num_allow > 0 or num_sitemap > 0: # robots.txt contains some entries, show browsable list! :)
                for Display, Links in EntriesList:
                        TestResult += self.Core.PluginHelper.DrawResourceLinkList( Display, Links )
        TestResult += str(NumAddedURLs) + " URLs have been added and classified"
        return TestResult

    def GetTransactionStats( self, NumMatchedTransactions , NumTotalTransactions):
        Percentage = round( NumMatchedTransactions * 100 / max( NumTotalTransactions, 1 ), 2 )
        StatsStr = str( NumMatchedTransactions ) + " out of " + str( NumTotalTransactions ) + " (" + str( Percentage ) + "%)"
        return [ Percentage, StatsStr ]

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

    def ResearchHeaders( self, RegexName ):
        RegexName, Transactions, TotalTransac = self.Core.DB.Transaction.SearchByRegexName(RegexName)
        NuTransactions = len(Transactions)
        Percentage, StatsStr = self.GetTransactionStats( len(Transactions), TotalTransac )
        template = Template( """
        <table class="table table-bordered table-striped ">
            <thead>
                <tr>
                    <th class="text-center" colspan="2">
                        Header Analysis Summary
                    </th>
                </tr>
            </thead>
            <tbody>
                <tr>
                        <th>Log</th>
                        <td><a href="../{{ HTMLTransacLogLink }}" class="button" target="_blank">
                                <span> See log </span>
                                </a>
                        </td>
                </tr>
                <tr>
                        <th>HTTP Transaction Stats</th>
                        <td class='alt'> {{ StatsStr }} matched </td>
                </tr>
        </tbody>
        </table>
        
        <div class="alert alert-info"><strong>NOTE!</strong> Only <u>unique values per header</u> are shown with a link to an example transaction</div>
        <table class="table table-bordered table-striped"> 
            <thead>
                <tr>
            <th class="text-center" colspan="2">
                Header Value Analysis
            </th>
        </tr>
            </thead>
                <tbody>
                <tr>
                        <th> Header </th> 
                        <th> Values </th>
                </tr>
                {% for Header in HeaderList %}
                                <tr>
                                        <td> {{ Header }} </td>
                                        <td>
                                                {% if Header|lower not in  HeaderDict %}
                                                        Not Found
                                                {% else %}
                                                        {% for HeaderValue in HeaderDict[Header|lower] %}
                                                                <a href="./{{ Header2TransacDict[Header|lower + HeaderValue] }}" class="label" target="_blank">
                                                                        {{ HeaderValue }}
                                                                </a>
                                                                <br />
                                                        {% endfor %}
                                                {% endif %}
                                        </td>
                                        
                                </tr>

                {tao% endfor %}
            </tbody>
        </table>
        """ )

        vars = {
                                "HTMLTransacLogLink":self.Core.Config.GetHTMLTransaclog( False ),
                                "StatsStr": StatsStr,
                                "HeaderList":self.Core.GetHeaderList(RegexName),
                                }


        return(template.render( vars ))


    def CookieAttributeAnalysis( self, CookieValueList, Header2TransacDict ):
        template = Template( """
        <h3>Cookie Attribute Analysis</h3>
        <table class="report_intro"> 
                {% for Cookie in Cookies %}
                        <tr>
                                <th colspan="2">
                                        Cookie: 
                                        <a href="{{ Cookie.Link }}" class="button" target="_blank">
                                                <span> {{ Cookie.Name }} </span>
                                        </a>
                                </th>
                        </tr>
                        <tr>
                                <th>Attribute</th>
                                <th>Value</th>
                        </tr>
                        <tr>
                                <td>Value</td>
                                <td>{% if CookieAttribs[0] %} 
                                                {{ CookieAttribs[0] }}
                                        {% else %}
                                                <b>Not Found</b>
                                        {% endif %}
                                </td>
                        </tr>
                {% endfor %}
        </table>
        """ )

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

    def FingerprintData(self):
        AllValues, HeaderTable , HeaderDict, Header2TransacDict, NuTransactions = self.ResearchHeaders(self.Core.Config.GetHeaderList('HEADERS_FOR_FINGERPRINT'))
        for Value in AllValues:
                HeaderTable += self.DrawVulnerabilitySearchBox(Value) # Add Vulnerability search boxes after table
        return HeaderTable
