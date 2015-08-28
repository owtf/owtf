#!/usr/bin/env python
'''
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
