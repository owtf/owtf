#!/usr/bin/env python2
"""
tests.runner
~~~~~~~~~~~~

Tests runner.
"""

import sys
from os import path as os_path
from sys import path as sys_path
import unittest


def include():
    """Include owtf/ in python sys path."""
    framework_path = os_path.abspath(".")
    sys_path.append(framework_path)


if __name__ == "__main__":
    include()
    from tests.suite.parser import get_suites

    suite = get_suites(sys.argv[1:])
    unittest.TextTestRunner(verbosity=3).run(suite)
