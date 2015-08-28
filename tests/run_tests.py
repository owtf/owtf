#!/usr/bin/env python
'''
This is the command-line tool for running tests.
'''

from testing_framework.runner.parser import ArgumentParser
from testing_framework.runner.arg_builder import NoseArgumentBuilder
from testing_framework.runner.runner import Runner
from sys import argv
from os import path as os_path
from sys import path as sys_path


def include_owtf_path_in_pythonpath():
    framework_path = os_path.abspath('..')
    print "[+] Setting up environment..."
    sys_path.append(framework_path)
    print framework_path + " appended to the PYTHON_PATH"


include_owtf_path_in_pythonpath()
parser = ArgumentParser()
if (len(argv) == 1):
    parser.print_usage()
else:
    args = parser.parse_arguments(argv[1:len(argv)])
    nose_arguments = NoseArgumentBuilder(args).build()
    runner = Runner(nose_arguments)
    print "[+] Running tests..."
    if (args.coverage is not None) and (args.all == True):
        # Coverage reports only have sense with all test
        runner.run_nose_with_coverage()
    else:
        runner.run_nose()
