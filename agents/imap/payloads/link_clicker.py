#!/usr/bin/env python
'''
Description: OWTF imap agent daemon plugin, to emulate user clicks via email
'''

import re
import subprocess

# TODO: Play with below and see if it is better or not
# http://daringfireball.net/2009/11/liberal_regex_for_matching_urls
# url_regex = re.compile(r'\b(([\w-]+://?|www[.])[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/)))')
URL_REGEX = 'http[:0-9a-zA-Z\.\/]+'


def run(params):
    log_str = " >> %s 2>> %s" % (params['log'], params['error_log'])
    for url in re.findall(URL_REGEX, str(params['message'])):
        print "Found URL=%s" % url
        visit_url_cmd = "curl %s" % url
        subprocess.Popen(visit_url_cmd, shell=True) # Visit URL
        # Log visit
        subprocess.Popen('echo "$(date)" - %s' % (VisitURLCmd+LogStr), shell=True)
