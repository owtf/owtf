"""

Decorators for any i/o standard functions.
Useful to catch any permission problems.

"""


import os
import shutil
import logging
import errno


def catch_perm(func):
    """Decorator on I/O functions.

    If an error access due to permissions is detected, force OWTF to quit
    properly.

    """
    def io_perm(core, name, *args, **kwargs):
        """Call the original function while checking for perm errors.

        Now each function needs the Core object in order to properly quit.

        """
        try:
            return func(name, *args, **kwargs)
        except (OSError, IOError) as e:
            if e.errno == errno.EACCES:
                core.Error.FrameworkAbort(
                    "Perm error when calling '%s'! "
                    "Please check the rights on '%s'." % (func.__name__, name))
            else:
                raise e
    return io_perm


# Decorated functions.
# From os.
mkdir = catch_perm(os.mkdir)
makedirs = catch_perm(os.makedirs)
# From shutil.
rmtree = catch_perm(shutil.rmtree)
# From logging.
FileHandler = catch_perm(logging.FileHandler)
