from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

TransactionBase = declarative_base()

class Transaction(TransactionBase):
	__tablename__ = "transactions"

	id = Column(Integer, primary_key = True)
	url = Column(String)
	method = Column(String)
	request_headers = Column(String)
	raw_request = Column(String)
	request_body = Column(String)
	response_code = Column(Integer)
	response_headers = Column(String)
	response_body = Column(String)
	vulnerability = Column(Boolean, default = False)

	def __repr__(self):
		return "<HTTP Transaction (url='%s' method='%s' response_code='%d')>"%(self.url, self.method, self.response_code)

URLBase = declarative_base()

class Url(URLBase):
	__tablename__ = "urls"

	url = Column(String, primary_key = True)
	visited = Column(Boolean, default = True)
	scheme = Column(String)

	def __repr__(self):
		return "<URL (url='%s')>"%(self.url)

TargetBase = declarative_base()

class Target(TargetBase):
	__tablename__ = "targets"

	url = Column(String, primary_key = True)
	ip = Column(String)
	port = Column(Integer)
	scheme = Column(String)
	ips = Column(String)
	host_name = Column(String)
	ip_url = Column(String)
	root_domain = Column(String)
	transaction_db = Column(String)
	url_db = Column(String)

	def __repr__(self):
		return "<Target (url='%s')>"%(self.url)

ErrorBase = declarative_base()

class Error(ErrorBase):
	__tablename__ = "errors"

	id = Column(Integer, primary_key = True)
	owtf_message = Column(String, nullable = True)
	exc_type = Column(String)
	exc_traceback = Column(String)
	user_message = Column(String, nullable = True)
	reported = Column(Boolean, default = False)

	def __repr__(self):
		return "<Error (traceback='%s')>"%(self.traceback)

Base = declarative_base()

class WebPlugin(Base):
	__tablename__ = "plugins"

	id = Column(String, primary_key = True) # OWTF Code
	path = Column(String)
	user_plugin = Column(Boolean, default = False)

class WebProfile(Base):
	__tablename__ = "profiles"

	id = Column(Integer, primary_key = True)
	plugins = Column(String)