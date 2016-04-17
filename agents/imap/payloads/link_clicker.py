#!/usr/bin/env python
'''
Description:
OWTF imap agent daemon plugin, to emulate user clicks via email
'''

import re
import subprocess

URL_REGEX = 'http[:0-9a-zA-Z\.\/]+'
# TODO: Play with below and see if it is better or not
# http://daringfireball.net/2009/11/liberal_regex_for_matching_urls


def Run(params):
    LogStr = " >> %s 2>> %s" % (params['Log'], params['ErrorLog'])
    for URL in re.findall(URL_REGEX, str(params['Message'])):
        print "Found URL=%s" % URL
        VisitURLCmd = "curl %s" % URL
        subprocess.Popen(VisitURLCmd, shell=True)  # Visit URL
        # Log visit:
        subprocess.Popen('echo "$(date)" - %s%s' % (VisitURLCmd, LogStr), shell=True)
