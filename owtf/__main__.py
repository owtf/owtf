"""
owtf.main
~~~~~~~~~

A __main__ method for OWTF tool so that it can be called as a module
"""

import sys

from owtf.main import start


def main():
    start(sys.argv)

if __name__ == "__main__":
    main()
