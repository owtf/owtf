"""
owtf
~~~~~
"""
from .db.database import get_scoped_session


__version__ = '2.3b'
__release__ = 'MacOWTF'


db = get_scoped_session()
