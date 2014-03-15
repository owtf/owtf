from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

TransactionBase = declarative_base()

class Transaction(TransactionBase):
	__tablename__ = "transactions"

	id = Column(Integer, primary_key = True)
	url = Column(String)
	scope = Column(Boolean, default = False)
	method = Column(String)
	request_headers = Column(String)
	raw_request = Column(String)
	request_body = Column(String, nullable = True)
	response_code = Column(Integer)
	response_headers = Column(String)
	response_body = Column(String, nullable = True)
	vulnerability = Column(Boolean, default = False)

	def __repr__(self):
		return "<HTTP Transaction (url='%s' method='%s' response_code='%d')>"%(self.url, self.method, self.response_code)

URLBase = declarative_base()

class Url(URLBase):
	__tablename__ = "urls"

	url = Column(String, primary_key = True)
	visited = Column(Boolean, default = False)

	def __repr__(self):
		return "<URL (url='%s')>"%(self.url)

TargetBase = declarative_base()

class Target(TargetBase):
	__tablename__ = "targets"

	target_url = Column(String, primary_key = True)
	host_ip = Column(String)
	port_number = Column(Integer)
	open_ports = Column(String, nullable = True)
	url_scheme = Column(String)
	host_ips = Column(String, nullable = True) # Comma seperated
	host_name = Column(String)
	host_path = Column(String)
	ip_url = Column(String)
	top_domain = Column(String)

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

ReviewWebBase = declarative_base()

class SemiPassivePluginOutput(ReviewWebBase):
	__tablename__ = "semipassive"

	id = Column(String, primary_key = True) # OWTF Code
	output = Column(String)
	user_notes = Column(String, nullable = True)
	user_ranking = Column(Integer, nullable = True)
	owtf_ranking = Column(Integer, nullable = True)

class ActivePluginOutput(ReviewWebBase):
	__tablename__ = "active"

	id = Column(String, primary_key = True) # OWTF Code
	output = Column(String)
	user_notes = Column(String, nullable = True)
	user_ranking = Column(Integer, nullable = True)
	owtf_ranking = Column(Integer, nullable = True)

class PassivePluginOutput(ReviewWebBase):
	__tablename__ = "passive"

	id = Column(String, primary_key = True)
	output = Column(String)
	user_notes = Column(String, nullable = True)
	user_ranking = Column(Integer, nullable = True)
	owtf_ranking = Column(Integer, nullable = True)

ResourceBase = declarative_base()

class Resource(ResourceBase):
	__tablename__ = "resources"

	id = Column(Integer, primary_key = True)
	dirty = Column(Boolean, default = False) # Dirty if user edited it. Useful while updating
	resource_name = Column(String)
	resource_type = Column(String)
	resource = Column(String)

GeneralBase = declarative_base()

class ConfigSetting(GeneralBase):
	__tablename__ = "configuration"

	key = Column(String, primary_key = True)
	value = Column(String)
	dirty = Column(Boolean, default = False)
