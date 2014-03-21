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
import os
import re
import cgi
import json
from jinja2 import Template
from framework.lib.general import *
from collections import defaultdict
import logging

PLUGIN_OUTPUT = {"Type":None, "Output":None} # This will be json encoded and stored in db as string

class PluginHelper:
        mNumLinesToShow = 25

        def __init__( self, CoreObj ):
                self.Core = CoreObj
                # Compile regular expressions only once on init:
                self.RobotsAllowRegexp = re.compile( "Allow: ([^\n  #]+)" )
                self.RobotsDisallowRegexp = re.compile( "Disallow: ([^\n #]+)" )
                self.RobotsSiteMap = re.compile( "Sitemap: ([^\n #]+)" )

        def MultipleReplace( self, Text, ReplaceDict ): # This redundant method is here so that plugins can use it
                return MultipleReplace( Text, ReplaceDict )

        def CreateCommandTable(self, Command):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "CommandTable"
            plugin_output["output"] = {"Command" : Command}
            return(json.dumps(plugin_output))

        def DrawCommandTable( self, Command ):
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

        def CreateLinkList(self, LinkListName, Links):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "LinkList"
            plugin_output["output"] = {"LinkListName" : LinkListName, "Links" : Links}
            return(json.dumps(plugin_output))

        def DrawLinkList( self, LinkListName, Links ): # Wrapper to allow rendering a bunch of links -without name- as resource links with name = link
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

        def CreateResourceLinkList(self, ResourceListName, ResourceList):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "ResourceLinkList"
            plugin_output["output"] = {"ResourceListName": ResourceListName, "ResourceList":ResourceList}
            return(json.dumps(plugin_output))

        def DrawResourceLinkList( self, ResourceListName, ResourceList ): # Draws an HTML Search box for defined Vuln Search resources
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

        def CreateTabbedResourceLinkList(self, ResourceList):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "TabbedResourceLinkList"
            plugin_output["output"] = {"ResourceList" : ResourceList}
            return(json.dumps(plugin_output))

        def DrawTabbedResourceLinkList(self, ResourcesList):
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

        def CreateListPostProcessing(self, ResourceListName, LinkList, HTMLLinkList):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "ListPostProcessing"
            plugin_output["output"] = {"ResourceListName" : ResourceListName, "LinkList" : LinkList, "HTMLLinkList":HTMLLinkList}
            return(json.dumps(plugin_output))

        def DrawListPostProcessing( self, ResourceListName, LinkList, HTMLLinkList ):
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

        def RequestAndCreateLinkList(self, ResourceListName, ResourceList, PluginInfo):
            #for Name, Resource in Core.Config.GetResources('PassiveRobotsAnalysisHTTPRequests'):
            LinkList = []
            for Name, Resource in ResourceList:
                Chunks = Resource.split( '###POST###' )
                URL = Chunks[0]
                POST = None
                Method = 'GET'
                if len( Chunks ) > 1: # POST
                        Method = 'POST'
                        POST = Chunks[1]
                        Transaction = self.Core.Requester.GetTransaction( True, URL, Method, POST )
                if Transaction.Found:
                        RawHTML = Transaction.GetRawResponseBody()
                        FilteredHTML = self.Core.Reporter.Sanitiser.CleanThirdPartyHTML( RawHTML )
                        NotSandboxedPath = self.Core.PluginHandler.DumpPluginFile( "NOT_SANDBOXED_" + Name + ".html", FilteredHTML, PluginInfo )
                        log( "File: " + "NOT_SANDBOXED_" + Name + ".html" + " saved to: " + NotSandboxedPath )
                        iframe_template = Template( """
                        <iframe src="{{ NotSandboxedPath }}" sandbox="" security="restricted"  frameborder = '0' style = "overflow-y:auto; overflow-x:hidden;width:100%;height:100%;" >
                        Your browser does not support iframes
                        </iframe>
                        """ )
                        iframe = iframe_template.render( NotSandboxedPath = NotSandboxedPath.split( '/' )[-1] )
                        SandboxedPath = self.Core.PluginHandler.DumpPluginFile( "SANDBOXED_" + Name + ".html", iframe , PluginInfo )
                        log( "File: " + "SANDBOXED_" + Name + ".html" + " saved to: " + SandboxedPath )
                        LinkList.append( ( Name, SandboxedPath ) )
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "RequestLinkList"
            plugin_output["output"] = {"ResourceListName": ResourceListName, "LinkList" : LinkList}
            return(json.dumps(plugin_output))

        def RequestAndDrawLinkList( self, ResourceListName, LinkList ):
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

        def CreateVulnerabilitySearchBox(self, SearchStr):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "VulnerabilitySearchBox"
            plugin_output["output"] = {"SearchStr" : SearchStr}
            return(json.dumps(plugin_output))

        def DrawVulnerabilitySearchBox( self, SearchStr ): # Draws an HTML Search box for defined Vuln Search resources
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

        def CreateSuggestedCommandBox(self, PluginInfo, CommandCategoryList, Header = ''):
            plugin_output = dict(PLUGIN_OUTPUT)
            plugin_output["type"] = "SuggestedCommandBox"
            plugin_output["output"] = { "PluginInfo":PluginInfo, "CommandCategoryList":CommandCategoryList, "Header":Header}
            return(json.dumps(plugin_output))

        def DrawSuggestedCommandBox( self, PluginInfo, CommandCategoryList, Header = '' ): # Draws HTML tabs for a list of TabName => Resource Group (i.e. how to run hydra, etc)
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

        def SetConfigPluginOutputDir( self, PluginInfo ):
                PluginOutputDir = self.Core.PluginHandler.GetPluginOutputDir( PluginInfo )
                self.Core.DB.Target.SetPath( 'PLUGIN_OUTPUT_DIR', os.getcwd() + '/' + PluginOutputDir ) # FULL output path for plugins to use
                self.Core.Shell.RefreshReplacements() # Get dynamic replacement, i.e. plugin-specific output directory
                return PluginOutputDir

        def InitPluginOutputDir( self, PluginInfo ):
                PluginOutputDir = self.SetConfigPluginOutputDir( PluginInfo )
                self.Core.CreateMissingDirs( PluginOutputDir ) # Create output dir so that scripts can cd to it :)
                return PluginOutputDir

        def RunCommand( self, Command, PluginInfo, PluginOutputDir ):
                FrameworkAbort = PluginAbort = False
                if not PluginOutputDir:
                        PluginOutputDir = self.InitPluginOutputDir( PluginInfo )
                self.Core.Timer.StartTimer( 'FormatCommandAndOutput' )
                ModifiedCommand = self.Core.Shell.GetModifiedShellCommand( Command, PluginOutputDir )
                try:
                        RawOutput = self.Core.Shell.shell_exec_monitor( ModifiedCommand )

                except PluginAbortException, PartialOutput:
                        RawOutput = str( PartialOutput.parameter ) # Save Partial Output
                        PluginAbort = True
                except FrameworkAbortException, PartialOutput:
                        RawOutput = str( PartialOutput.parameter ) # Save Partial Output
                        FrameworkAbort = True

                TimeStr = self.Core.Timer.GetElapsedTimeAsStr('FormatCommandAndOutput')
                log("Time="+TimeStr)
                return [ ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir ]

        def GetCommandOutputFileNameAndExtension( self, InputName ):
                OutputName = InputName
                OutputExtension = "txt"
                if InputName.split( '.' )[-1] in [ 'html' ]:
                        OutputName = InputName[0:-5]
                        OutputExtension = "html"
                return [ OutputName, OutputExtension ]

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

        def EscapeSnippet( self, Snippet, Extension ):
                if Extension == "html": # HTML
                        return str( Snippet )
                return cgi.escape( str( Snippet ) ) # Escape snippet to avoid breaking HTML

        def DrawCommandDump( self, Name, CommandIntro, ModifiedCommand, FilePath, OutputIntro, OutputLines, TimeStr):
        #def FormatCommandAndOutput( self, Name, CommandIntro, ModifiedCommand, FilePath, OutputIntro, OutputLines, TimeStr):
                #ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir = self.RunCommand( Command, PluginInfo, PluginOutputDir )
            table_vars = {
                            "Name": Name,
                            "CommandIntro" : CommandIntro ,
                            "ModifiedCommand": ModifiedCommand,
                            "FilePath" : FilePath,
                            "OutputIntro":  OutputIntro,
                            "OutputLines": OutputLines,
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

        def CreateCommandDump(self, CommandIntro, OutputIntro, ResourceList, PluginInfo, PreviousOutput):
            output_list = []
            PluginOutputDir = self.InitPluginOutputDir( PluginInfo )
            for Name, Command in ResourceList:
                plugin_output = dict(PLUGIN_OUTPUT)
                ModifiedCommand, FrameworkAbort, PluginAbort, TimeStr, RawOutput, PluginOutputDir = self.RunCommand( Command, PluginInfo, PluginOutputDir )
                plugin_output["type"] = "CommandDump"
                plugin_output["output"] = {
                                "Name": self.GetCommandOutputFileNameAndExtension( Name )[0],
                                "CommandIntro" : CommandIntro ,
                                "ModifiedCommand": ModifiedCommand,
                                "FilePath" : self.Core.PluginHandler.DumpPluginFile( Name, RawOutput, PluginInfo ),
                                "OutputIntro":  OutputIntro,
                                "OutputLines": UnicodeRawOutput.split( "\n" )[:self.mNumLinesToShow],
                                "TimeStr": TimeStr
                        }
                if Name == self.Core.Config.Get( 'EXTRACT_URLS_RESERVED_RESOURCE_NAME' ): # This command returns URLs for processing
                # The plugin_output output dict will be remade if the resource is of this type
                        plugin_output = self.LogURLsFromStr( RawOutput )
                if self.Core.Config.Get( 'UPDATE_REPORT_AFTER_EACH_COMMAND' ) == 'Yes':
                        self.Core.Reporter.SavePluginReport( Content, PluginInfo ) # Keep updating the report after each command/scanner runs
                if PluginAbort: # Pass partial output to external handler:
                        raise PluginAbortException( PreviousOutput + Content )
                if FrameworkAbort:
                        raise FrameworkAbortException( PreviousOutput + Content )
                try:
                    UnicodeRawOutput = unicode(RawOutput, "utf-8")
                except TypeError: # Already unicode
                    UnicodeRawOutput = RawOutput
                output_list.append(plugin_output)
            return(output_list)

        #def DrawCommandDump( self, DumpDict, NumLinesToShow = 5 ):
                # Content = LinkToPluginOutputDir = '<br />'+self.Core.Reporter.Render.DrawButtonLink('Browse Plugin Output Files', self.Core.GetPartialPath(PluginOutputDir))+'<br />' <- This is now in the Plugin report box
                #content = ''
                #for CommandOutput in DumpDict: #Command = Resource.strip()
                #        Content += self.FormatCommandAndOutput( CommandIntro, OutputIntro, Name, Command, PluginInfo, PluginOutputDir )
                #return Content

        def LogURLsFromStr( self, RawOutput ):
                self.Core.Timer.StartTimer( 'LogURLsFromStr' )
                URLList = RawOutput.strip().split( "\n" )
                self.Core.DB.URL.ImportURLs( URLList ) # Extract and classify URLs and store in DB
                NumFound = 0
                VisitURLs = False
                if self.Core.PluginHandler.IsActiveTestingPossible(): # Can visit new URLs found to feed DB straightaway
                        VisitURLs = True
                        for Transaction in self.Core.Requester.GetTransactions( True, self.Core.DB.URL.GetURLsToVisit( URLList ) ): # Visit all URLs if not in Cache
                                if Transaction.Found:
                                        NumFound += 1
                TimeStr = self.Core.Timer.GetElapsedTimeAsStr('LogURLsFromStr')
                log("Spider/URL scaper time="+TimeStr)
                plugin_output["type"] = "URLsFromStr"
                plugin_output["output"] = {"TimeStr":TimeStr, "VisitURLs":VisitURLs, "URLList":URLList, "NumFound":NumFound}
                return(plugin_output)

        def DrawURLsFromStr(self, TimeStr, VisitURLs, URLList, NumFound):
                Table = self.Core.Reporter.Render.CreateTable({'class' : 'commanddump'})
                Table.CreateCustomRow('<tr><th colspan="2">Spider/URL scraper</th></tr>')
                Table.CreateRow(['Time', 'URL stats'], True)
                Table.CreateRow([TimeStr, self.Core.Reporter.Render.DrawHTMLList(['Visited URLs?: '+str(VisitURLs), str(len(URLList))+' URLs scraped', str(NumFound)+' URLs found'])])
                return Table.Render()

        def DumpFile( self, Filename, Contents, PluginInfo, LinkName = '' ):
                save_path = self.Core.PluginHandler.DumpPluginFile( Filename, Contents, PluginInfo )
                if not LinkName:
                        LinkName = save_path
                log("File: "+Filename+" saved to: "+save_path)          
                template = Template( """
                        <a href="{{ Link }}" target="_blank">
                                {{ LinkName }}
                        </a>
                """ )
                return [ save_path, template.render( LinkName = LinkName, Link = "../../../" + save_path ) ]

        def DumpFileGetLink( self, Filename, Contents, PluginInfo, LinkName = '' ):
                return self.DumpFile( Filename, Contents, PluginInfo, LinkName )[1]

        def AnalyseRobotsEntries( self, Contents ): # Find the entries of each kind and count them
                num_lines = len( Contents.split( "\n" ) ) # Total number of robots.txt entries
                AllowedEntries = list(set(self.RobotsAllowRegexp.findall( Contents ))) # list(set()) is to avoid repeated entries
                num_allow = len( AllowedEntries ) # Number of lines that start with "Allow:"
                DisallowedEntries = list(set(self.RobotsDisallowRegexp.findall( Contents )))
                num_disallow = len( DisallowedEntries ) # Number of lines that start with "Disallow:"
                SitemapEntries = list(set(self.RobotsSiteMap.findall( Contents )))
                num_sitemap = len( SitemapEntries ) # Number of lines that start with "Sitemap:"
                NotStr = ''
                if 0 == num_allow and 0 == num_disallow and 0 == num_sitemap:
                        NotStr = 'NOT '
                return [ num_lines, AllowedEntries, num_allow, DisallowedEntries, num_disallow, SitemapEntries, num_sitemap , NotStr ]

        def ProcessRobots( self, PluginInfo, Contents, LinkStart, LinkEnd, Filename = 'robots.txt' ):
                plugin_output = dict(PLUGIN_OUTPUT)
                plugin_output["Type"] = "Robots"
                num_lines, AllowedEntries, num_allow, DisallowedEntries, num_disallow, SitemapEntries, num_sitemap, NotStr = self.AnalyseRobotsEntries( Contents )
                SavePath = self.Core.PluginHandler.DumpPluginFile( Filename, Contents, PluginInfo )
                TopURL = self.Core.DB.Target.Get( 'TOP_URL' )
                if num_disallow > 0 or num_allow > 0 or num_sitemap > 0: # robots.txt contains some entries, show browsable list! :)
                        self.Core.DB.URL.AddURLsStart()
                        EntriesList = []
                        for Display, Entries in [ [ 'Disallowed Entries', DisallowedEntries ], [ 'Allowed Entries', AllowedEntries ], [ 'Sitemap Entries', SitemapEntries ] ]:
                                Links = [] # Initialise category-specific link list
                                for Entry in Entries:
                                        if 'Sitemap Entries' == Display:
                                                URL = Entry
                                                self.Core.DB.URL.AddURL( URL ) # Store real links in the DB
                                                Links.append( [ Entry, Entry ] ) # Show link in defined format (passive/semi_passive)
                                        else:
                                                URL = TopURL + Entry
                                                self.Core.DB.URL.AddURL( URL ) # Store real links in the DB
                                                Links.append( [ Entry, LinkStart + Entry + LinkEnd ] ) # Show link in defined format (passive/semi_passive)
                                EntriesList.append(( Display, Links ))
                NumAddedURLs = self.Core.DB.URL.AddURLsEnd()
                plugin_output["output"] = { "NotStr":NotStr,
                                            "NumLines":num_lines,
                                            "NumAllow":num_allow,
                                            "NumDisallow":num_disallow,
                                            "NumSitemap":num_sitemap,
                                            "SavePath":SavePath,
                                            "NumAddedURLs":NumAddedURLs,
                                            "EntriesList":EntriesList
                                            }
                return(json.dumps(plugin_output))

        def DrawRobots(self, NotStr, NumLines, NumAllow, NumDisallow, NumSitemap, SavePath, NumAddedURLs, EntriesList)
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

        def DrawTransactionTableForURLList( self, UseCache, URLList, Method = '', Data = '' ):
                return self.Core.Reporter.DrawHTTPTransactionTable( self.Core.Requester.GetTransactions( UseCache, URLList, Method, Data ) )

        def GetTransactionStats( self, NumMatchedTransactions ):
                TotalTransac = self.Core.DB.Transaction.GetNumTransactionsInScope()
                Percentage = round( NumMatchedTransactions * 100 / max( TotalTransac, 1 ), 2 )
                StatsStr = str( NumMatchedTransactions ) + " out of " + str( TotalTransac ) + " (" + str( Percentage ) + "%)"
                return [ NumMatchedTransactions, TotalTransac, Percentage, StatsStr ]

        def CreateMatchTable( self ):
                Table = self.Core.Reporter.Render.CreateTable( {'class' : 'transaction_log'} )
                Table.CreateRow( ['ID', 'Links', 'Match'], True )
                return Table

        def CreateMatchTables( self, Num ):
                TableList = []
                for x in range( 0, Num ):
                        TableList.append( self.CreateMatchTable() )
                return TableList

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

        def FindResponseHeaderMatchesForRegexp(self, HeaderRegexp, PluginInfo):
                return self.DrawResponseMatchesTables(self.Core.DB.Transaction.GrepResponseHeadersRegexp(HeaderRegexp), PluginInfo)

        def FindResponseHeaderMatchesForRegexps(self, HeaderRegexpList, PluginInfo):
                Result = ""
                for HeaderRegexp in HeaderRegexpList:
                        Result += self.FindResponseHeaderMatchesForRegexp(HeaderRegexp, PluginInfo)
                return Result

        def FindMultilineResponseMatchesForRegexp( self, ResponseRegexp, PluginInfo ):
                return self.DrawResponseMatchesTables( self.Core.DB.Transaction.GrepMultiLineResponseRegexp( ResponseRegexp ), PluginInfo )

        def FindMultilineResponseMatchesForRegexps( self, ResponseRegexpList, PluginInfo ):
                Result = ""
                for ResponseRegexp in ResponseRegexpList:
                        #print "ResponseRegexp="+str(ResponseRegexp)
                        Result += self.FindMultilineResponseMatchesForRegexp( ResponseRegexp, PluginInfo )
                return Result

        def FindHeaders( self, HeaderList ):
                HeaderDict = defaultdict( list )
                HeaderLines = []
                AllValues = []
                Header2TransacDict = {}
                TransactionFiles = []
                Command, Headers = self.Core.DB.Transaction.GrepHeaders( HeaderList )
                for Header in Headers.split( "\n" ):
                        TransacFile = Header.split( ":" )[0]
                        HeaderLine = Header.replace( TransacFile + ":", "" ).strip()
                        if not HeaderLine:
                                continue #Skip blank lines
                        HeaderName = HeaderLine.split( ':' )[0]
                        HeaderValue = HeaderLine.replace( HeaderName + ": ", "" ).strip() # Replace respecting case!
                        if 'No such file or directory' == HeaderValue:
                                continue # Skip garbage errors
                        if TransacFile not in TransactionFiles: # Count unique transactions
                                TransactionFiles.append( TransacFile )
                        if HeaderLine in HeaderLines:
                                continue # Skip already processed headers
                        HeaderLines.append( HeaderLine )
                        HeaderName = HeaderName.lower() # Now force lowercase to ensure match later!
                        HeaderDict[HeaderName].append( HeaderValue )
                        AllValues.append( HeaderValue )
                        Header2TransacDict[HeaderName + HeaderValue] = TransacFile
                return [ Command, HeaderDict, AllValues, Header2TransacDict , len( TransactionFiles ) ]

        def ResearchHeaders( self, HeaderList ):
                Command, HeaderDict, AllValues, Header2TransacDict, NuTransactions = self.FindHeaders( HeaderList )
                NuTransactions, TotalTransac, Percentage, StatsStr = self.GetTransactionStats( NuTransactions )
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
                        <tr>
                                <th>Analysis Command</th>
                                <td><pre>{{ Command|e }}</pre></td>
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
                                        "Command": Command,
                                        "HeaderList":HeaderList,
                                        "HeaderDict": HeaderDict,
                                        "Header2TransacDict": Header2TransacDict,
                                        }


                return [ AllValues, template.render( vars ), HeaderDict, Header2TransacDict , NuTransactions ]


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
                                        
        def ResearchFingerprintInlog(self):
                log("Researching Fingerprint in Log ..")
                AllValues, HeaderTable , HeaderDict, Header2TransacDict, NuTransactions = self.ResearchHeaders(self.Core.Config.GetHeaderList('HEADERS_FOR_FINGERPRINT'))
                for Value in AllValues:
                        HeaderTable += self.DrawVulnerabilitySearchBox(Value) # Add Vulnerability search boxes after table
                return HeaderTable 
