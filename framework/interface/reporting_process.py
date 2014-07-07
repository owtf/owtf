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

The reporting process is responsible for calling report generation function after fixed amount of time
'''
import os
import time

class reporting_process:
        
    def start(self,Core,reporting_time,queue):
        """
        This function after each 1 second checks if the owtf execution is completed
        if yes it calls generate_reports if not then after every reporting_time second it calls 
        generate_reports
        """
        filename = Core.Config.Get('PLUGIN_REPORT_REGISTER')
        self.core = Core
        #filesize of plugin register file
        self.filesize=0
        #number of plugins in pluginregister till now
        self.num_plugins=0
        #if plugin register file from previous runs is present then skip that many plugins
        if os.path.exists(filename):
            self.filesize = os.path.getsize(filename)
            with self.core.open(filename) as f:
                lines = f.read().splitlines()
            self.num_plugins=len(lines)

        try:
            start_time = time.time() # A variable to keep track of when last report update occured
            # Check if Queue is empty. If not, poison pill is sent
            while queue.empty():
                if (time.time() - start_time) > reporting_time:
                    self.generate_reports(filename)
                    start_time = time.time() # Updating the variable for next check
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.generate_reports(filename)

    def generate_reports(self,filename):
        """
        This function takes plugin_register filename and checks if it exists and if it exists then 
        if its size has been changed from last call then this means there is a new plugin executed and it generates
        the report by calling reportFinish()
        """
        if os.path.exists(filename):
            #check if there some new entry in plugin file
            if os.path.getsize(filename)>self.filesize:
                self.filesize = os.path.getsize(filename)
                with self.core.open(filename) as f:
                    lines = f.read().splitlines()
                i=1
                #mapping of targets to new plugins
                new_urls = {}
                #for each new entry
                for line in lines:
                    #if plugin has been processed already then skip it
                    if i>self.num_plugins:
                        target = line.split("||")[4].strip()
                        #get plugin required in reportFinish() 
                        plugin = self.register_entry_to_plugin(line)
                        if target not in new_urls:
                            new_urls[target]=[]
                        new_urls[target].append(plugin)
                    i=i+1
                #call report finish function for each target
                for target in new_urls:
                    self.core.Reporter.ReportFinish(target,new_urls[target])
                self.num_plugins=i
                
                        
    def register_entry_to_plugin(self,line):
        """
        This function converts plugin register entry to Plugin structure needed for 
        reportFinish() function
        """
        
        plugin_entry = line.split("||")
        plugin = {}
        plugin['Code'] = plugin_entry[0].strip()
        plugin['Group'] = plugin_entry[2].strip()
        plugin['Target'] = plugin_entry[4].strip()
        plugin['ReviewOffset'] = plugin_entry[4].strip()
        plugin['Args']=plugin_entry[5].strip()
        plugin['Label'] = plugin_entry[1].strip()
        plugin['Start']=plugin_entry[7].strip()
        plugin['Path']=plugin_entry[3].strip()
        plugin['End'] = plugin_entry[8].strip()
        plugin['Runtime'] = plugin_entry[9].strip()
        plugin['Type'] = plugin_entry[1].strip()
        return plugin
        
        
