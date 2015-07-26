from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Table, Column, Integer, String, Boolean,\
    Float, DateTime, ForeignKey, Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# This table actually allows us to make a many to many relationship
# between transactions table and grep_outputs table
target_association_table = Table(
    'target_session_association',
    Base.metadata,
    Column('target_id', Integer, ForeignKey('targets.id')),
    Column('session_id', Integer, ForeignKey('sessions.id'))
)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    active = Column(Boolean, default=False)
    targets = relationship(
        "Target",
        secondary=target_association_table,
        backref="sessions")


class Target(Base):
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
    transactions = relationship("Transaction", cascade="delete")
    poutputs = relationship("PluginOutput", cascade="delete")
    urls = relationship("Url", cascade="delete")
    commands = relationship("Command", cascade="delete")
    # Also has a column session specified as backref in
    # session model
    works = relationship("Work", backref="target", cascade="delete")

    @hybrid_property
    def max_user_rank(self):
        user_ranks = [-1]
        user_ranks += [poutput.user_rank for poutput in self.poutputs]
        return(max(user_ranks))

    @hybrid_property
    def max_owtf_rank(self):
        owtf_ranks = [-1]
        owtf_ranks += [poutput.owtf_rank for poutput in self.poutputs]
        return(max(owtf_ranks))

    def __repr__(self):
        return "<Target (url='%s')>" % (self.target_url)


# This table actually allows us to make a many to many relationship
# between transactions table and grep_outputs table
transaction_association_table = Table(
    'transaction_grep_association',
    Base.metadata,
    Column('transaction_id', Integer, ForeignKey('transactions.id')),
    Column('grep_output_id', Integer, ForeignKey('grep_outputs.id'))
)


class Transaction(Base):
    __tablename__ = "transactions"

    target_id = Column(Integer, ForeignKey("targets.id"))
    id = Column(Integer, primary_key=True)
    url = Column(String)
    scope = Column(Boolean, default=False)
    method = Column(String)
    data = Column(String, nullable=True)  # Post DATA
    time = Column(Float(precision=10))
    time_human = Column(String)
    local_timestamp = Column(DateTime)
    raw_request = Column(Text)
    response_status = Column(String)
    response_headers = Column(Text)
    response_size = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    binary_response = Column(Boolean, nullable=True)
    session_tokens = Column(String, nullable=True)
    login = Column(Boolean, nullable=True)
    logout = Column(Boolean, nullable=True)
    grep_outputs = relationship(
        "GrepOutput",
        secondary=transaction_association_table,
        cascade="delete",
        backref="transactions")

    def __repr__(self):
        return "<HTTP Transaction (url='%s' method='%s' response_status='%s')>" % (self.url, self.method, self.response_status)


class GrepOutput(Base):
    __tablename__ = "grep_outputs"

    target_id = Column(Integer, ForeignKey("targets.id"))
    id = Column(Integer, primary_key=True)
    name = Column(String)
    output = Column(Text)
    # Also has a column transactions, which is added by
    # using backref in transaction

    __table_args__ = (UniqueConstraint('name', 'output', target_id),)


class Url(Base):
    __tablename__ = "urls"

    target_id = Column(Integer, ForeignKey("targets.id"))
    url = Column(String, primary_key=True)
    visited = Column(Boolean, default=False)
    scope = Column(Boolean, default=True)

    def __repr__(self):
        return "<URL (url='%s')>" % (self.url)


class PluginOutput(Base):
    __tablename__ = "plugin_outputs"

    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    # There is a column named plugin which is caused by backref
    # from the plugin class
    id = Column(Integer, primary_key=True)
    plugin_code = Column(String)  # OWTF Code
    plugin_group = Column(String)
    plugin_type = Column(String)
    date_time = Column(DateTime, default=datetime.datetime.now())
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    output = Column(String, nullable=True)
    error = Column(String, nullable=True)
    status = Column(String, nullable=True)
    user_notes = Column(String, nullable=True)
    user_rank = Column(Integer, nullable=True, default=-1)
    owtf_rank = Column(Integer, nullable=True, default=-1)
    output_path = Column(String, nullable=True)

    @hybrid_property
    def run_time(self):
        return(self.end_time - self.start_time)

    __table_args__ = (UniqueConstraint('plugin_key', 'target_id'),)


class Command(Base):
    __tablename__ = "command_register"

    start_time = Column(DateTime)
    end_time = Column(DateTime)
    success = Column(Boolean, default=False)
    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    modified_command = Column(String)
    original_command = Column(String, primary_key=True)

    @hybrid_property
    def run_time(self):
        return(self.end_time - self.start_time)


class Error(Base):
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True)
    owtf_message = Column(String)
    traceback = Column(String, nullable=True)
    user_message = Column(String, nullable=True)
    reported = Column(Boolean, default=False)

    def __repr__(self):
        return "<Error (traceback='%s')>" % (self.traceback)


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    dirty = Column(Boolean, default=False)  # Dirty if user edited it. Useful while updating
    resource_name = Column(String)
    resource_type = Column(String)
    resource = Column(String)
    __table_args__ = (UniqueConstraint('resource', 'resource_type', 'resource_name'),)


class ConfigSetting(Base):
    __tablename__ = "configuration"

    key = Column(String, primary_key=True)
    value = Column(String)
    section = Column(String)
    descrip = Column(String, nullable=True)
    dirty = Column(Boolean, default=False)

    def __repr__(self):
        return "<ConfigSetting (key='%s', value='%s', dirty='%r')>" % (self.key, self.value, self.dirty)


class TestGroup(Base):
    __tablename__ = "test_groups"

    code = Column(String, primary_key=True)
    group = Column(String)  # web, net
    descrip = Column(String)
    hint = Column(String, nullable=True)
    url = Column(String)
    priority = Column(Integer)
    plugins = relationship("Plugin")


class Plugin(Base):
    __tablename__ = "plugins"

    key = Column(String, primary_key=True)  # key = type@code
    title = Column(String)
    name = Column(String)
    code = Column(String, ForeignKey("test_groups.code"))
    group = Column(String)
    type = Column(String)
    descrip = Column(String, nullable=True)
    file = Column(String)
    attr = Column(String, nullable=True)
    works = relationship("Work", backref="plugin", cascade="delete")
    outputs = relationship("PluginOutput", backref="plugin")

    def __repr__(self):
        return "<Plugin (code='%s', group='%s', type='%s')>" % (self.code, self.group, self.type)

    @hybrid_property
    def min_time(self):
        """
        Consider last 5 runs only, better performance and accuracy
        """
        poutputs_num = len(self.outputs)
        if poutputs_num != 0:
            if poutputs_num < 5:
                run_times = [poutput.run_time for poutput in self.outputs]
            else:
                run_times = [poutput.run_time for poutput in self.outputs[-5:]]
            return(min(run_times))
        else:
            return None

    @hybrid_property
    def max_time(self):
        """
        Consider last 5 runs only, better performance and accuracy
        """
        poutputs_num = len(self.outputs)
        if poutputs_num != 0:
            if poutputs_num < 5:
                run_times = [poutput.run_time for poutput in self.outputs]
            else:
                run_times = [poutput.run_time for poutput in self.outputs[-5:]]
            return(max(run_times))
        else:
            return None

    __table_args__ = (UniqueConstraint('type', 'code'),)


class Work(Base):
    __tablename__ = "worklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    plugin_key = Column(String, ForeignKey("plugins.key"))
    active = Column(Boolean, default=True)
    # Columns plugin and target are created using backrefs

    __table_args__ = (UniqueConstraint('target_id', 'plugin_key'),)

    def __repr__(self):
        return "<Work (target='%s', plugin='%s')>" % (
            self.target_id, self.plugin_key)


class Mapping(Base):
    __tablename__ = 'mappings'

    owtf_code = Column(String, primary_key=True)
    mappings = Column(String)
    category = Column(String, nullable=True)


VulnexpBase = declarative_base()

class Vulnexp(VulnexpBase):
    __tablename__ = 'vulnexp'
    title = Column(String, primary_key=True)
    desc = Column(String)
    category = Column(String)
