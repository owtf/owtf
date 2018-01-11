"""
owtf
~~~~~
"""

from owtf.utils.file import FileOperations, get_logs_dir
from .db.database import get_scoped_session


__version__ = '2.3b'
__release__ = 'MacOWTF'

print("""\033[92m
    _____ _ _ _ _____ _____
    |     | | | |_   _|   __|
    |  |  | | | | | | |   __|
    |_____|_____| |_| |__|
    
        @owtfp
    http://owtf.org
    Version: {0}
    Release: {1}
    \033[0m""".format(__version__, __release__)
)


db = get_scoped_session()
FileOperations.create_missing_dirs(get_logs_dir())

