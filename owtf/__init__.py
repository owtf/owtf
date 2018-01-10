"""
owtf
~~~~~
"""
from owtf.utils.file import FileOperations, get_logs_dir
from .db.database import get_scoped_session


__version__ = '2.3b'
__release__ = 'MacOWTF'


FileOperations.create_missing_dirs(get_logs_dir())
db = get_scoped_session()
