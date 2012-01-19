#!/usr/bin/env python
'''
Tries to put links around nikto findings to save a bit of time in manual verification

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
'''

import sys, os, re

if len(sys.argv) < 3:
	print "Usage: "+sys.argv[0]+" <nikto.txt file> <top_url>"
	exit(-1)

OSVDB_regexp = re.compile("\+ (OSVDB-[0-9]+):.*")
URL_regexp = re.compile("(/[^ :]*):")
LinkList = []
TopURL = sys.argv[2]
origin = sys.argv[1]
destination = 'Nikto_Verify.html'
# Generate html output directly to stdout, looks better in the report
with open(destination, 'w') as file:
	#file.write("<html><title>Nikto Verification</title><body><pre>\n")
	#print "<html><title>Nikto Verification</title><body><pre>\n"
	print "<pre>"
	for line in open(origin).read().split("\n"):
		newline = line.strip()
	
		for match in URL_regexp.findall(line):
			URL = TopURL+match
			if URL not in LinkList:
				LinkList.append(URL)
			URL_LINK = '<a href="'+URL+'" target="_blank">'+match+'</a>'
			newline = newline.replace(match, URL_LINK)

		for match in OSVDB_regexp.findall(line):
			OSVDBID = match.split('-')[1]
			OSVDB_URL = 'http://osvdb.org/show/osvdb/'+OSVDBID
			OSVDB_LINK = '<a href="'+OSVDB_URL+'" target="_blank">'+match+'</a>'
			newline = newline.replace(match, OSVDB_LINK)
			if OSVDB_URL not in LinkList:
				LinkList.append(OSVDB_URL)
		print newline
	print "</pre>"
		#file.write(newline+"\n")
	#file.write("</pre></body></html>\n")
#print 'A verification file has been generated <a href="'+os.path.abspath(destination)+'" target="_blank">here</a>'
