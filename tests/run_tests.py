#!/usr/bin/env python
"""
This is the command-line tool for running tests.
"""
import os
import sys
from testing_framework.runner.parser import ArgumentParser
from testing_framework.runner.arg_builder import NoseArgumentBuilder
from testing_framework.runner.runner import Runner


framework_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
print "[+] Setting up environment..."
sys.path.append(framework_path)
print framework_path + " appended to the PYTHON_PATH"

parser = ArgumentParser()
if len(sys.argv) == 1:
    parser.print_usage()
else:
    args = parser.parse_arguments(sys.argv[1:])
    nose_arguments = NoseArgumentBuilder(args).build()
    runner = Runner(nose_arguments)
    print "[+] Running tests..."
    if args.coverage is not None and args.all:
        # Coverage reports only have sense with all test
        runner.run_nose_with_coverage()
    else:
        runner.run_nose()
