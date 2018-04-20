"""
owtf.models.transaction
~~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, Text, ForeignKey, Table, Index
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model

# This table actually allows us to make a many to many relationship
# between transactions table and grep_outputs table
transaction_association_table = Table('transaction_grep_association', Model.metadata,
                                      Column('transaction_id', Integer, ForeignKey('transactions.id')),
                                      Column('grep_output_id', Integer, ForeignKey('grep_outputs.id')))

Index('transaction_id_idx', transaction_association_table.c.transaction_id, postgresql_using='btree')


class Transaction(Model):
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
        "GrepOutput", secondary=transaction_association_table, cascade="delete", backref="transactions")

    def __repr__(self):
        return "<HTTP Transaction (url='{!s}' method='{!s}' response_status='{!s}')>".format(
            self.url, self.method, self.response_status)
