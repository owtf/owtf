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
