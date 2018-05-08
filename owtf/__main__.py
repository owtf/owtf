"""
owtf.__main__
~~~~~~~~~~~~~
A __main__ method for OWTF so that internal services can be called as Python modules.
"""
import sys

from owtf.core import main as owtf_main


def main():
    owtf_main(sys.argv)


if __name__ == "__main__":
    main()
