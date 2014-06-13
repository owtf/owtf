from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
import datetime

TransactionBase = declarative_base()


class Transaction(TransactionBase):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    url = Column(String)
    scope = Column(Boolean, default=False)
    method = Column(String)
    data = Column(String, nullable=True)  # Post DATA
    time = Column(Float(precision=10))
    time_human = Column(String)
    raw_request = Column(String)
    response_status = Column(String)
    response_headers = Column(String)
    response_body = Column(String, nullable=True)
    binary_response = Column(Boolean, nullable=True)
    grep_output = Column(String, nullable=True)

    def __repr__(self):
        return "<HTTP Transaction (url='%s' method='%s' response_status='%s')>" % (self.url, self.method, self.response_status)

URLBase = declarative_base()


class Url(URLBase):
    __tablename__ = "urls"

    url = Column(String, primary_key=True)
    visited = Column(Boolean, default=False)
    scope = Column(Boolean, default=True)

    def __repr__(self):
        return "<URL (url='%s')>" % (self.url)

TargetBase = declarative_base()


class Target(TargetBase):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_url = Column(String, unique=True)
    host_ip = Column(String)
    port_number = Column(String)
    url_scheme = Column(String)
    alternative_ips = Column(String, nullable=True)  # Comma seperated
    host_name = Column(String)
    host_path = Column(String)
    ip_url = Column(String)
    top_domain = Column(String)
    top_url = Column(String)
    scope = Column(Boolean, default=True)

    def __repr__(self):
        return "<Target (url='%s')>" % (self.target_url)

ErrorBase = declarative_base()


class Error(ErrorBase):
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True)
    owtf_message = Column(String)
    traceback = Column(String, nullable=True)
    user_message = Column(String, nullable=True)
    reported = Column(Boolean, default=False)

    def __repr__(self):
        return "<Error (traceback='%s')>" % (self.traceback)

OutputBase = declarative_base()


class PluginOutput(OutputBase):
    __tablename__ = "plugin_outputs"

    key = Column(String, primary_key=True)  # Key = plugin_type@code
    plugin_code = Column(String)  # OWTF Code
    plugin_group = Column(String)
    plugin_type = Column(String)
    date_time = Column(DateTime, default=datetime.datetime.now())
    start_time = Column(String)
    end_time = Column(String)
    execution_time = Column(String)
    output = Column(String, nullable=True)
    error = Column(String, nullable=True)
    status = Column(String, nullable=True)
    user_notes = Column(String, nullable=True)
    user_rank = Column(Integer, nullable=True)
    owtf_rank = Column(Integer, nullable=True)
    output_path = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint('plugin_type', 'plugin_code'),)

RegisterBase = declarative_base()


class Command(RegisterBase):
    __tablename__ = "command_register"

    start = Column(String)
    end = Column(String)
    run_time = Column(String)
    success = Column(Boolean, default=False)
    target = Column(Integer)
    modified_command = Column(String)
    original_command = Column(String, primary_key=True)

ResourceBase = declarative_base()


class Resource(ResourceBase):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    dirty = Column(Boolean, default=False)  # Dirty if user edited it. Useful while updating
    resource_name = Column(String)
    resource_type = Column(String)
    resource = Column(String)
    __table_args__ = (UniqueConstraint('resource', 'resource_type', 'resource_name'),)

GeneralBase = declarative_base()


class ConfigSetting(GeneralBase):
    __tablename__ = "configuration"

    key = Column(String, primary_key=True)
    value = Column(String)
    section = Column(String)
    descrip = Column(String, nullable=True)
    dirty = Column(Boolean, default=False)

    def __repr__(self):
        return "<ConfigSetting (key='%s', value='%s', dirty='%r')>" % (self.key, self.value, self.dirty)

PluginBase = declarative_base()


class TestGroup(PluginBase):
    __tablename__ = "test_groups"

    code = Column(String, primary_key=True)
    group = Column(String)  # web, net
    descrip = Column(String)
    hint = Column(String, nullable=True)
    url = Column(String)
    plugins = relationship("Plugin")


class Plugin(PluginBase):
    __tablename__ = "plugins"

    key = Column(String, primary_key=True)  # key = type@code
    title = Column(String)
    name = Column(String)
    code = Column(String, ForeignKey('test_groups.code'))
    group = Column(String)
    type = Column(String)
    descrip = Column(String, nullable=True)
    file = Column(String)
    attr = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint('type', 'code'),)
