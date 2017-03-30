import os
import sys

from framework.dependency_check import verify_dependencies


"""
Checks if the script is running inside a virtualenv or not
Stolen from http://stackoverflow.com/questions/1871549/python-determine-if-running-inside-virtualenv
Inside a virtualenv, sys.prefix points to the virtualenv directory,
and sys.real_prefix points to the "real" prefix of the system Python (often /usr or /usr/local or some such).

Outside the virtualenv, sys.real_prefix does not exist.
"""
if not hasattr(sys, 'real_prefix'):
    print("[-] It seems that virtualenv has not been activated!\n")
    print("[-] Please run: \t source ~/.%src; workon owtf\n" % os.environ["SHELL"].split(os.sep)[-1])
    sys.exit(1)

verify_dependencies(os.path.dirname(os.path.abspath(sys.argv[0])) or '.')
