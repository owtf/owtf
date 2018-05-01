"""
owtf.models.target
~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Boolean, Column, Integer, String, Index, ForeignKey, Table
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model

# This table actually allows us to make a many to many relationship
# between transactions table and grep_outputs table
target_association_table = Table(
    "target_session_association",
    Model.metadata,
    Column("target_id", Integer, ForeignKey("targets.id")),
    Column("session_id", Integer, ForeignKey("sessions.id")),
)

Index("target_id_idx", target_association_table.c.target_id, postgresql_using="btree")


class Target(Model):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_url = Column(String, unique=True)
    host_ip = Column(String)
    port_number = Column(String)
    url_scheme = Column(String)
    alternative_ips = Column(String, nullable=True)  # Comma separated
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
    # Also has a column session specified as backref in session model
    works = relationship("Work", backref="target", cascade="delete")

    @hybrid_property
    def max_user_rank(self):
        user_ranks = [-1]
        user_ranks += [poutput.user_rank for poutput in self.poutputs]
        return max(user_ranks)

    @hybrid_property
    def max_owtf_rank(self):
        owtf_ranks = [-1]
        owtf_ranks += [poutput.owtf_rank for poutput in self.poutputs]
        return max(owtf_ranks)

    @classmethod
    def get_indexed(cls, session):
        results = session.query(Target.id, Target.target_url).all()
        return results

    def __repr__(self):
        return "<Target (url='{!s}')>".format(self.target_url)
