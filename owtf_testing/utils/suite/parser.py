from __future__ import print_function
import sys
import argparse
import unittest

from owtf_testing.utils.suite import SUITES


def create_parser():
    """Create the different options for running the functional testing framework."""
    parser = argparse.ArgumentParser(
        description="""OWASP OWTF - Functional Testing Framework.""")

    parser.add_argument(
        '-l', '--list',
        dest='list_suites',
        default=False,
        action='store_true',
        help='List the available test suites.')
    parser.add_argument(
        '-s', '--suite',
        dest='suite',
        default='all',
        help='Name of the suite to test.')
    return parser


def print_list_suites():
    categories = set()
    for suite in SUITES:
        if hasattr(suite, 'categories'):
            for el in suite.categories:
                categories.add(el)
    print('List of the available test suites:')
    print('\t all')
    for cat in categories:
        print('\t', cat)
    sys.exit(0)


def add_tests_to_suite(suite, opt):
    new_suite = []
    if 'all' in opt:
        new_suite = SUITES[:]
    else:
        for test_case in SUITES:
            if hasattr(test_case, 'categories') and opt in test_case.categories:
                new_suite.append(test_case)
    for test_case in new_suite:
        for method in dir(test_case):
            if method.startswith('test_'):
                suite.addTest(test_case(method))


def get_suites(args):
    """Run the functional testing framework according to the parameters."""
    suite = unittest.TestSuite()
    options = create_parser().parse_args(args)
    if options.list_suites:
        print_list_suites()
    if options.suite:
        add_tests_to_suite(suite, options.suite)
    return suite
