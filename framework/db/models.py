from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

TransactionBase = declarative_base()

class Transaction(TransactionBase):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key = True)
    url = Column(String)
    scope = Column(Boolean, default = False)
    method = Column(String)
    data = Column(String, nullable = True) # Post DATA
    time = Column(Float(precision = 20))
    time_human = Column(String)
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
    port_number = Column(String)
    url_scheme = Column(String)
    alternative_ips = Column(String, nullable = True) # Comma seperated
    host_name = Column(String)
    host_path = Column(String)
    ip_url = Column(String)
    top_domain = Column(String)
    top_url = Column(String)

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

class PluginOutput(ReviewWebBase):
    __tablename__ = "plugin_outputs"

    code = Column(String, primary_key = True) # OWTF Code
    plugin_type = Column(String)
    output = Column(String)
    user_notes = Column(String, nullable = True)
    user_ranking = Column(Integer, nullable = True)
    owtf_ranking = Column(Integer, nullable = True)

class ActivePluginOutput(ReviewWebBase):
    __tablename__ = "active"

    code = Column(String, primary_key = True) # OWTF Code
    output = Column(String)
    user_notes = Column(String, nullable = True)
    user_ranking = Column(Integer, nullable = True)
    owtf_ranking = Column(Integer, nullable = True)

class PassivePluginOutput(ReviewWebBase):
    __tablename__ = "passive"

    code = Column(String, primary_key = True)
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

PluginBase = declarative_base()

class TestCode(PluginBase):
    __tablename__ = "test_codes"

    code = Column(String, primary_key = True)
    group = Column(String) # web, net
    descrip = Column(String)
    hint = Column(String, nullable = True)
    url = Column(String)
    plugins = relationship("Plugin")

class Plugin(PluginBase):
    __tablename__ = "plugins"

    key = Column(String, primary_key = True) # Key = plugin_type@code
    plugin_title = Column(String)
    plugin_name = Column(String)
    plugin_code = Column(String, ForeignKey('test_codes.code'))
    plugin_group = Column(String)
    plugin_type = Column(String)
    plugin_descrip = Column(String, nullable = True)
    plugin_file = Column(String)
