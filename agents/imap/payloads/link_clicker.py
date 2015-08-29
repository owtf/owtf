#!/usr/bin/env python
'''
Description:
OWTF imap agent daemon plugin, to emulate user clicks via email
'''
import re, subprocess
URL_REGEX = 'http[:0-9a-zA-Z\.\/]+'
#TODO: Play with below and see if it is better or not
# http://daringfireball.net/2009/11/liberal_regex_for_matching_urls
#url_regex = re.compile(r'\b(([\w-]+://?|www[.])[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/)))')

def Run(Params):
	LogStr = " >> " + Params['Log'] + " 2>> " + Params['ErrorLog']
	for URL in re.findall(URL_REGEX, str(Params['Message'])):
		print "Found URL=" + URL
		VisitURLCmd = "curl " + URL
		subprocess.Popen(VisitURLCmd, shell=True) # Visit URL
		# Log visit:
		subprocess.Popen('echo "$(date)" - ' + VisitURLCmd + LogStr, shell=True)
