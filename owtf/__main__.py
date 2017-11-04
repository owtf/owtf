"""
owtf.main
~~~~~~~~~

A __main__ method for OWTF tool so that it can be called as a module
"""

import sys

from owtf.cli import main as owtf_main


def main():
    owtf_main(sys.argv)

if __name__ == "__main__":
    main()
