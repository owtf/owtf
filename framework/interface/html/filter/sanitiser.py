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

The sanitiser module allows the rest of the framework to sanitise input
Requires lxml, installation instructions here: http://lxml.de/installation.html
In Backtrack 5: /usr/bin/easy_install --allow-hosts=lxml.de,*.python.org lxml
Tip for Ubuntu courtesy of Mario Heiderich: Python2.7-dev is needed to compile this lib properly 
Clean HTML reference: http://lxml.de/lxmlhtml.html#cleaning-up-html
Library documentation: http://lxml.de/api/lxml.html.clean.Cleaner-class.html
'''
import sys
from lxml.html.clean import Cleaner, clean_html
import lxml.html
from urlparse import urlparse
ALLOWED_TAGS = ('html', 'body', 'a', 'p', 'h1', 'h2', 'h3', 'h4', 'div', 'span', 'i', 'b', 'u', 'table', 'tbody', 'tr', 'td', 'th', 'strong', 'em', 'sup', 'sub', 'ul', 'ol', 'li')
ALLOWED_URL_SCHEMES = [ 'http', 'https', 'ftp', 'mailto', 'sftp', 'shttp' ]

class HTMLSanitiser:
	def __init__(self):
		self.Cleaner = Cleaner(scripts = False, javascript = False, comments = False, links = False, meta = True, page_structure = False, processing_instructions = False, embedded = False, frames = False, forms = False, annoying_tags = False, remove_unknown_tags = False, safe_attrs_only = True, allow_tags=ALLOWED_TAGS)
		#self.Cleaner = Cleaner(allow_tags=ALLOWED_TAGS, remove_unknown_tags=False)

	def IsValidURL(self, URL):
		ParsedURL = urlparse(URL)
		return (ParsedURL.scheme in ALLOWED_URL_SCHEMES)

	def CleanURLs(self, HTML): 
		# Largely Inspired from: http://stackoverflow.com/questions/5789127/how-to-replace-links-using-lxml-and-iterlinks
		ParsedHTML = lxml.html.document_fromstring(HTML)
		#print dir(ParsedHTML)
		#'iter', 'iterancestors', 'iterchildren'
		#for Element in ParsedHTML.iterchildren():
		#	print dir(Element)
		#	print Element.tag
		for Element, Attribute, Link, Pos in ParsedHTML.iterlinks():
			if not self.IsValidURL(Link):
				Element.set(Attribute, Link.replace(Link, ''))
		return lxml.html.tostring(ParsedHTML)

	def CleanThirdPartyHTML(self, HTML): 
		# 1st clean URLs, 2nd get rid of basics, 3rd apply white list
		return self.Cleaner.clean_html(clean_html(self.CleanURLs(HTML)))

	def TestPrint(self, TestInfo, TestOutput):
		TestInfo += "_" * (60 - len(TestInfo)) # Make info visually easier to compare
		print TestInfo + TestOutput

# For testing as a standalone script:
if 'sanitiser.py' in sys.argv[0]: # When called as a script run tests
	Sanitiser = HTMLSanitiser()
	Input = sys.stdin.read() # Read for stdin so that we can cat whatever | sanitiser => easier to test in bulk
	Sanitiser.TestPrint("raw input=", Input)
	Sanitiser.TestPrint("Filter 1 - clean_html=", clean_html(Input))
	Sanitiser.TestPrint("Filter 2 - white_list=", Sanitiser.Cleaner.clean_html(Input))
	Sanitiser.TestPrint("Filter 3 - clean_html(white_list) =", clean_html(Sanitiser.Cleaner.clean_html(Input)))
	Sanitiser.TestPrint("Filter 4 = cleanURLs(clean_html(white_list)) =", Sanitiser.CleanURLs(clean_html(Sanitiser.Cleaner.clean_html(Input))))
	Sanitiser.TestPrint("Filter 5 = cleanURLs(white_list(clean_html)) =", Sanitiser.CleanURLs(Sanitiser.Cleaner.clean_html(clean_html(Input))))
	Sanitiser.TestPrint("Filter 6 = white_list(clean_html(cleanURLs))", Sanitiser.Cleaner.clean_html(clean_html(Sanitiser.CleanURLs(Input))))
	Sanitiser.TestPrint("Latest - Step 1 - CleanURLs =", Sanitiser.CleanURLs(Input))
	Sanitiser.TestPrint("Latest - Step 2 - clean_html(CleanURLs) =", clean_html(Sanitiser.CleanURLs(Input)))
	Sanitiser.TestPrint("Latest - Step 3 - white_list(clean_html(CleanURLs)) =", Sanitiser.CleanThirdPartyHTML(Input))
"""
#WIP below
, remove_tags = None
hash(x)
 	allow_tags = None
hash(x)
 	kill_tags = None
hash(x)
 	remove_unknown_tags = True
 	safe_attrs_only = True
 	add_nofollow = False
 	host_whitelist = ()
 	whitelist_tags = set(['embed', 'iframe'])
 	_tag_link_attrs = {'a': 'href', 'applet': ['code', 'object'], 
"""
