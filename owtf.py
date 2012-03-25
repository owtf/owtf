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

This is the command-line front-end in charge of processing arguments and call the framework
'''
import getopt, sys, os

RootDir = os.path.dirname(os.path.abspath(sys.argv[0])) or '.' # Get tool path from script path

from framework import core
from framework.lib.general import *

def Banner():
	print """
                  __       ___  
                 /\ \__  /'___\ 
  ___   __  __  _\ \ ,_\/\ \__/ 
 / __`\/\ \/\ \/\ \\ \ \/\ \ ,__\ 
/\ \_\ \ \ \_/ \_/ \\ \ \_\ \ \_/
\ \____/\ \___x___/'\ \__\\\ \_\ 
 \/___/  \/__//__/   \/__/ \/_/ 

Offensive (Web) Testing Framework: An OWASP+PTES-focused try to unite great tools and make pen testing more efficient @owtfp http://owtf.org
Author: Abraham Aranguren <name.surname@gmail.com> - http://7-a.org - Twitter: @7a_
"""

def Usage(ErrorMessage):
	FullPath = sys.argv[0].strip()
	Main = FullPath.split('/')[-1]
	print "Current Path: "+FullPath
	print "Syntax: "+Main+" [ options ] <target1 target2 target3 ..> where target can be: <target URL / hostname / IP>"
	print "					NOTE: targets can also be provided via a text file\n"
	print " -l <web/net/aux>:		list available plugins in the plugin group (web, net or aux)"
	print " -f:				force plugin result overwrite (default is avoid overwrite)"
	print " -i <yes/no>			interactive: yes (default, more control) / no (script-friendly)"
	print " -e <except plugin1,2,..>	comma separated list of plugins to be ignored in the test"
	print " -o <only plugin1,2,..>	comma separated list of the only plugins to be used in the test"
	print " -p (ip:)port            setup an inbound proxy for manual site analysis"
	print " -x ip:port			send all owtf requests using the proxy for the given ip and port"
	print " -s 				Do not do anything, simply simulate how plugins would run"
	print " -m <g:f,w:f,n:f,r:f> 		Use my profile: 'f' = valid config file. g: general config, w: web plugin order, n: net plugin order, r: resources file"
	print " -a <depth/breadth> 		Multi-target algorithm: breadth (default)=each plugin runs for all targets first | depth=all plugins run for each target first"
	print ""
	print " -g <web/net/aux> 		Initial plugin group: web (default) = targets are interpreted as URLs = web assessment only"
	print "				net = targets are interpreted as hosts/network ranges = traditional network discovery and probing"
	print "				aux = targets are NOT interpreted, it is up to the plugin/resource definition to decide what to do with the target"
	print ""
	print " -t <plugin type>		For web plugins: passive, semi_passive, quiet (passive + semi_passive), grep, active, all (default)"
	print "				NOTE: grep plugins run automatically after semi_passive and active in the default profile"
	print "\nExamples:\n"
	print "Run all web plugins: 						"+Main+" http://my.website.com"
	print "Run only passive + semi_passive plugins:		 	"+Main+" -t quiet http://my.website.com"
	print "Run only active plugins: 					"+Main+" -t active http://my.website.com"
	print ""
	print "Run all plugins except 'OWASP-CM-001: Testing_for_SSL-TLS':	"+Main+" -e 'OWASP-CM-001' http://my.website.com"
	print "Run all plugins except 'OWASP-CM-001: Testing_for_SSL-TLS':	"+Main+" -e 'Testing_for_SSL-TLS' http://my.website.com"
	print ""
	print "Run only 'OWASP-CM-001: Testing_for_SSL-TLS': 			"+Main+" -o 'OWASP-CM-001' http://my.website.com"
	print "Run only 'OWASP-CM-001: Testing_for_SSL-TLS': 			"+Main+" -o 'Testing_for_SSL-TLS' http://my.website.com"
	print ""
	print "Run only OWASP-IG-005 and OWASP-WU-VULN:	 		"+Main+" -o 'OWASP-IG-005,OWASP-WU-VULN' http://my.website.com"
	print "Run using my resources file and proxy:	 		"+Main+" -m r:/home/me/owtf_resources.cfg -x 127.0.0.1:8080 http://my.website.com"
	print "\nERROR: "+ErrorMessage
	exit(-1)

def ValidatePluginGroup(PluginGroup):
	if PluginGroup not in [ 'web', 'net', 'aux' ]:
		Usage("Invalid Plugin Group: '"+str(PluginGroup)+"'")
	return PluginGroup

def ValidateOnePluginGroup(PluginGroups):
	if len(PluginGroups) > 1:
		Usage("The plugins specified belong to several Plugin Groups: '"+str(PluginGroups)+"'")

def ProcessOptions(argv, Core):
	try:
		opts, args = getopt.getopt(argv,"a:g:t:e:o:i:x:p:m:l:sf") # Don't forget the ":" at the end :) -IF YOU EXPECT A VALUE!! ;)-
	except getopt.GetoptError:
		Usage("Invalid OWTF option(s)")

	# Default settings:
	PluginType = 'all' 
	Simulation = ForceOverwrite = False
	Interactive = True
	InboundProxy = OutboundProxy = OnlyPlugins = ExceptPlugins = ListPlugins = None 
	Algorithm = 'breadth'
	PluginGroup = 'web'
	Profiles = []
	for opt,arg in opts:
		if opt == '-c':
			PluginType = arg
		if opt == '-a':
			Algorithm = arg
			if Algorithm not in Core.Config.Get('ALGORITHMS'):#[ 'breadth', 'depth' ]:
				Usage("Invalid Algorithm")
		if opt == '-g':
			PluginGroup = ValidatePluginGroup(arg)
		if opt == '-t':
			PluginType = arg
			#if PluginType not in [ 'semi_passive', 'passive', 'active', 'grep' ]:
			if PluginType != 'all' and PluginType != 'quiet' and PluginType not in Core.Config.Plugin.GetAllTypes():
				Usage("Invalid Plugin Type '"+str(PluginType)+"'")
		elif opt == '-l':
			ListPlugins = True
			PluginGroup = ValidatePluginGroup(arg)
		elif opt == '-s':
			Simulation = True
		elif opt == '-f':
			ForceOverwrite = True
		elif opt == '-i':
			if arg == 'no':
				Interactive = False
#		elif opt == '-t': # Threads = to be implemented
#			TargetURL = arg
		elif opt == '-m': # Custom profiles specified
			for Profile in arg.split(','): # Quick pseudo-validation check
				Chunks = Profile.split(':')
				if len(Chunks) != 2 or not os.path.exists(Chunks[1]):
					Usage("Invalid Profile")
				else: # Profile "ok" :)
					Profiles.append(Chunks)
		elif opt == '-o':
			OnlyPlugins = arg.split(',')
			PluginGroups = Core.Config.Plugin.GetGroupsForPlugins(OnlyPlugins)
			ValidateOnePluginGroup(PluginGroups)
			try:
				PluginGroup = PluginGroups[0] # Set Plugin Group according to plugin list specified
			except IndexError:
				Usage("Please use either OWASP/OWTF codes or Plugin names")
			cprint("Defaulting Plugin Group to '"+PluginGroup+"' based on list of plugins supplied")
		elif opt == '-e':
			ExceptPlugins = arg.split(',')
			PluginGroups = Core.Config.Plugin.GetGroupsForPlugins(ExceptPlugins)
			ValidateOnePluginGroup(PluginGroups)
		elif opt == '-x':
			OutboundProxy = arg.split(':')
			if len(OutboundProxy) != 2: # OutboundProxy should be ip:port
				Usage()
		elif opt == '-p':
			InboundProxy = arg.split(':')
			if len(InboundProxy) not in [ 1, 2]: # OutboundProxy should be (ip:)port
				Usage()

	if PluginGroup == 'net':
		Usage('Sorry, net plugins are not implemented yet')
	PluginTypesForGroup = Core.Config.Plugin.GetTypesForGroup(PluginGroup)
	if PluginType == 'all':
		PluginType = PluginTypesForGroup
	elif PluginType == 'quiet':
		PluginType = [ 'passive', 'semi_passive' ]
		if PluginGroup != 'web':
			Usage("The quiet plugin type can only be used for the web plugin group currently")
	elif PluginType not in PluginTypesForGroup:
		Usage("Invalid Plugin Type '"+str(PluginType)+"' for Plugin Group '"+str(PluginGroup)+"'. Valid Types: "+', '.join(PluginTypesForGroup))

	Scope = args # Arguments at the end are the URL target(s)
	NumTargets = len(Scope)
	if PluginGroup != 'aux' and NumTargets == 0 and not ListPlugins:
		Usage("The scope must specify at least one target")
	elif NumTargets == 1: # Check if this is a file
		if os.path.exists(Scope[0]):
			cprint("The scope provided is a file, trying to load targets from it ..")
			NewScope = []
			for Target in open(Scope[0]).read().split("\n"):
				CleanTarget = Target.strip()
				if not CleanTarget:
					continue # Skip blank lines
				NewScope.append(CleanTarget)
			if len(NewScope) == 0: # Bad file
				Usage("Please provide a scope file where each line is a target")
			Scope = NewScope

	for Target in Scope:
		if Target[0] == "-":
			Usage("Invalid Target: "+Target)

	Args = ''
	if PluginGroup == 'aux':
		Args = Scope # For Aux plugins, the Scope are the parameters
		Scope = ['aux'] # Aux plugins do not have targets, they have metasploit-like parameters

	try:
		if Core.Start( { 
					'ListPlugins' : ListPlugins
					, 'Force_Overwrite' : ForceOverwrite
					, 'Interactive' : Interactive
					, 'Simulation' : Simulation
					, 'Scope' : Scope
					, 'argv' : sys.argv
					, 'PluginType' : PluginType
					, 'OnlyPlugins' : OnlyPlugins
					, 'ExceptPlugins' : ExceptPlugins
					, 'InboundProxy' : InboundProxy
					, 'OutboundProxy' : OutboundProxy
					, 'Profiles' : Profiles
					, 'Algorithm' : Algorithm
					, 'PluginGroup' : PluginGroup
					, 'Args' : Args } ): # Only if Start is for real (i.e. not just listing plugins, etc)
			Core.Finish("Complete") # Not Interrupted or Crashed
	except KeyboardInterrupt: # NOTE: The user chose to interact, so no need to check if interactivity was chosen or not here:
		cprint("\nowtf was aborted by the user: Please check the report and plugin output files for partial results")
		Core.Finish("Aborted by user") # Interrupted. Must save the DB to disk, finish report, etc
	except SystemExit:
		pass # Report already saved, framework tries to exit
	except:
		Core.Error.Add("Unknown owtf error")
		Core.Finish("Crashed") # Interrupted. Must save the DB to disk, finish report, etc

Banner()
Core = core.Init(RootDir) # Initialise Framework
ProcessOptions(sys.argv[1:], Core)
