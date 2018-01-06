"""
owtf
~~~~~
"""
from owtf.db.database import Session, get_db_engine


__version__ = '2.3b'
__release__ = 'MacOWTF'

Session.configure(bind=get_db_engine())
db = Session()
