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

import nose  # @UnresolvedImport
import argparse
from sys import argv
from os import path as os_path
from sys import path as sys_path

TEST_CASES_FOLDER = "test_cases"

class ArgumentParser():

    def __init__(self):
        self.parser = self.create_parser()

    def create_parser(self):
        parser = argparse.ArgumentParser(description="OWTF Testing framework Command Line Tool")
        parser.add_argument("category", nargs="?", help="Category of the tests to run. The possible values are: plugin, framework and all (to run all the test suites)")
        parser.add_argument("-a", "--all", action="store_true", default=False, dest="all", help="This flag tells the framework to run all the tests associated to the selected category.")
        parser.add_argument("-m", "--modules", dest="modules", metavar="module1,module2...", help="Comma separated list of modules to run inside the current category.")
        parser.add_argument("-o", "--only", dest="only", metavar="file1.py,file2.py", help="Comma separated list of test cases to run.")
        parser.add_argument("-c", "--with-coverage", dest="coverage", action="store_true", default=None, help="Tell the runner to perform test coverage analysis.")
        return parser

    def parse_arguments(self, arguments):
        self.parsed_arguments = self.parser.parse_args(arguments)
        validArguments, message = self.arguments_are_valid()
        if (validArguments):
            return self.parsed_arguments
        else:
            print "Arguments are not valid: " + message
            self.print_usage()
            return None

    def arguments_are_valid(self):
        validArguments, message = self.validate_combinations()
        return validArguments, message

    def validate_combinations(self):
        validArguments, message = True, ""
        if (self.has_category()):
            if (self.all_modules() and self.has_module_restriction()):
                validArguments = False
                message = "--all option is not compatible with -m option."
            elif (self.has_only_restriction()):
                validArguments = False
                message = "Category is not compatible with -o option."
        elif (self.has_only_restriction() and (self.all_modules() or self.has_module_restriction())):
            validArguments = False
            message = "-o is not compatible with any other option."
        elif (self.all_tests() and (self.has_only_restriction() or self.has_module_restriction())):
            validArguments = False
            message = "when running all tests is not possible to apply restrictions."
        return validArguments, message

    def has_category(self):
        return self.parsed_arguments.category is not None

    def has_only_restriction(self):
        return self.parsed_arguments.only is not None

    def has_module_restriction(self):
        return self.parsed_arguments.modules is not None

    def all_modules(self):
        return self.parsed_arguments.all

    def all_tests(self):
        return self.parsed_arguments.category == "all"

    def print_usage(self):
        self.parser.print_usage()


def build_nose_arguments(args):
    nose_arguments = ""
    category = ""
    modules_path = []
    all_categories = ["framework", "plugin", "testing_framework"]
    if (args.category in all_categories):
        category += args.category
        nose_arguments = TEST_CASES_FOLDER + "/" + category + "/"
    if (args.modules is not None):
        modules = args.modules.split(",")
        for i in modules:
            modules_path.append(TEST_CASES_FOLDER + "/" + category + "/" + i + ".py")
        nose_arguments = " ".join(modules_path)
    if (args.only is not None):
        nose_arguments += args.only.replace(",", " ")
    if (args.all == True):
        nose_arguments = TEST_CASES_FOLDER + "/"
    nose_arguments += " --verbose --detailed-errors"
    print "The arguments passed are: " + nose_arguments
    return "nosetests " + nose_arguments


def include_owtf_path_in_pythonpath():
    framework_path = os_path.abspath('..')
    print "[+] Setting up environment..."
    sys_path.append(framework_path)
    print framework_path + " appended to the PYTHON_PATH"


def run_nose_with_coverage(args):
    from coverage import coverage
    framework_path = os_path.abspath('..')
    cov = coverage(source=[os_path.join(framework_path, "framework"),
                           os_path.join(framework_path, "tests/testing_framework")])
    cov.start()
    run_nose(args)
    cov.stop()
    print "Generating coverage reports..."
    cov.html_report(directory="cover")


def run_nose(args):
    nose.run(argv=nose_arguments.split(" "))


include_owtf_path_in_pythonpath()
parser = ArgumentParser()
if (len(argv) == 1):
    parser.print_usage()
else:
    args = parser.parse_arguments(argv[1:len(argv)])
    nose_arguments = build_nose_arguments(args)
    print "[+] Running tests..."
    if (args.coverage is not None) and (args.all == True):
        # Coverage reports only have sense with all test
        run_nose_with_coverage(nose_arguments)
    else:
        run_nose(nose_arguments)
