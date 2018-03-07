"""
owtf.utils.commands
~~~~~~~~~~~~~~~~~~~

"""

import os


def get_command(argv):
    """Format command to remove directory and space-separated arguments.

    :params list argv: Arguments for the CLI.

    :return: Arguments without directory and space-separated arguments.
    :rtype: list

    """
    return " ".join(argv).replace(argv[0], os.path.basename(argv[0]))
