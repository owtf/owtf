#############################################################
Copyright 2010 Sunera, LLC.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################
# Contact:		Chris Sullo
# Blog:			http://security.sunera.com/
#
# Program Name:		CMS Explorer
# Purpose:		Look for installed plugins/themes for a CMS
# Version:		1.0
# Code Repo:		http://code.google.com/p/cms-explorer/
# Dependencies: 	LibWhisker
#			Getopt::Long
#			OSVDB API Key (optional): http://osvdb.org/api/about
#############################################################
About
This program attempts to brute-force guess the plugins and themes
installed in a CMS by requesting each plugin or theme name and 
looking at the response codes. 

The software can currently brute force themes and plugins/modules in:
	Wordpress
	Drupal
	Joomla!
	Mambo
The lists for Wordpress and Drupal are pulled directly from their 
development repos, and Joomla/Mambo were lovingly hand carved.

Optionally, a "bootstrap proxy" can be specified, which is separate
from the normal request proxy. If the bsproxy is set, any found 
plugins or themes will be requested through this proxy, and any 
exploration requests (see below) will be sent through it as well. 
This is a useful option to send dirs/files through a proxy such as 
Burp or Paros.

If the -explore option is used, the SVN/CVS repo will be checked 
to get a list of possible file names for each installed theme or 
plugin. This list of files is then requested through the bsproxy 
so they can be further checked for security issues. This only works 
for Drupal and Wordpress as they provide central repositories for user 
submitted modules.

The -osvdb option will search osvdb.org for vulnerabilities in the
products installed components. You must create an account on 
osvdb.org and put your API key in a file named 'osvdb.key'. An account
gives you 100 queries per day, or make a donation for a higher limit.

#############################################################
Requirements
This program requires:
- Getopt::Long perl module
- LibWhisker (LW2) included, or from http://www.wiretrip.net/rfp/lw.asp
- OSVDB API Key (optional): http://osvdb.org/api/about

#############################################################
Limitations
- Plugin and theme names are from the base directory checked-in to the 
  Wordpress or Drupal repo. In some cases, this top-level directory 
  does *not* match the install directory name.
- Joomla! and Mambo do not have central repos for plugins or themes, 
  so they must be manually gathered. If you have a list, or even a few, 
  send them over or commit them to the source tree!

#############################################################
Options	
	-bsproxy+ 	Proxy to route findings through (format: host:ip
			or http://host:ip/, default port 80)
	-explore	Look for files in the theme/plugin dir
	-osvdb 		Search OSVDB.org for vulnerabilities
	-plugins	Look for plugins (default: on)
	-pluginfile+	Plugin file list
	-proxy+ 	Proxy for requests (format: host:ip or 
			http://host:ip/, default port 80)
	-themes		Look for themes (default: on)
	-themefile+	Theme file list (default: themes.txt)
	-type+*		CMS type: Drupal, Wordpress, Joomla, Mambo
	-update 	Update lists from Wordpress/Drupal (over-writes 
			text files)
	-url+*		Full url to app's base directory
	-verbosity+ 	1-3

#############################################################
Examples
- Test for Wordpress plugins/themes on example.com, low verbosity and 
  explore using the bootstrap proxy 'localhost' on port 8080
	./cms-explorer.pl -url http://example.com/ -v 1 -bsproxy \ 
		http://localhost:8080/ -explore -type wordpress

- Test for Wordpress themes on example.com using themelist.txt, full
  verbosity and explore using the bootstrap proxy 'localhost' on port 80
	./cms-explorer.pl -url http://example.com/ -v 3 -bsproxy localhost \
		-explore -themes -themefile themelist.txt -type wordpress

- Test for Drupal plugins/themes on example.com, quietly with no exploration
	./cms-explorer.pl -url http://example.com/ -type drupal

- Test for Mambo components
	./cms-explorer.pl -url http://example.com/ -type joomla
