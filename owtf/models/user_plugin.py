"""
owtf.models.user_plugin
~~~~~~~~~~~~~~~~~~~~~~~

SQLAlchemy model for community-uploaded plugins.

Design decisions:
  - approval_status uses a string enum ('pending', 'approved', 'rejected') instead
    of a PostgreSQL ENUM type so the table is usable with SQLite in tests too.
  - file_path stores the absolute path on disk so the runner can locate the file
    without an extra lookup.
  - version is a free-form string (e.g. "1.0.0") because plugins are self-versioned
    by their authors; we do not enforce SemVer at the DB layer.
  - tags is a comma-separated string for simplicity; a join table would be
    over-engineering for the initial release.
"""

import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model

APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"

VALID_APPROVAL_STATUSES = {APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED}

VALID_GROUPS = {"web", "network", "auxiliary"}
VALID_TYPES = {"active", "passive", "semi_passive", "external", "grep"}


class UserPlugin(Model):
    """Represents a community-uploaded plugin stored in the DB."""

    __tablename__ = "user_plugins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=True)
    group = Column(String(32), nullable=False, default="web")
    type = Column(String(32), nullable=False, default="passive")
    author = Column(String(128), nullable=False)
    file_path = Column(String(512), nullable=False)
    rating = Column(Float, default=0.0, nullable=False)
    approval_status = Column(String(16), default=APPROVAL_PENDING, nullable=False, index=True)
    rejection_reason = Column(Text, nullable=True)
    version = Column(String(32), default="1.0.0", nullable=False)
    tags = Column(String(256), nullable=True)
    execution_timeout = Column(Integer, default=300, nullable=False)
    memory_limit = Column(Integer, default=268435456, nullable=False)  # 256 MB
    is_public = Column(Boolean, default=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user = relationship("User", foreign_keys=[user_id], backref="uploaded_plugins")
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer = relationship("User", foreign_keys=[reviewed_by_user_id])
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return "<UserPlugin name={!r} status={!r}>".format(self.name, self.approval_status)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "group": self.group,
            "type": self.type,
            "author": self.author,
            "file_path": self.file_path,
            "rating": self.rating,
            "approval_status": self.approval_status,
            "rejection_reason": self.rejection_reason,
            "version": self.version,
            "tags": self.tags.split(",") if self.tags else [],
            "execution_timeout": self.execution_timeout,
            "memory_limit": self.memory_limit,
            "is_public": self.is_public,
            "user_id": self.user_id,
            "reviewed_by_user_id": self.reviewed_by_user_id,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_for_user(cls, session, user_id: int):
        """Return all plugins uploaded by a specific user."""
        return session.query(cls).filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    # ------------------------------------------------------------------
    # Class-level query helpers
    # ------------------------------------------------------------------

    @classmethod
    def get_approved(cls, session):
        return session.query(cls).filter_by(approval_status=APPROVAL_APPROVED).all()

    @classmethod
    def get_pending(cls, session):
        return session.query(cls).filter_by(approval_status=APPROVAL_PENDING).all()

    @classmethod
    def get_by_name(cls, session, name: str):
        return session.query(cls).filter_by(name=name).first()

    @classmethod
    def search(
        cls,
        session,
        category=None,
        group=None,
        plugin_type=None,
        min_rating=None,
        status=None,
        query=None,
        limit=50,
        offset=0,
    ):
        """Flexible query with optional filters."""
        q = session.query(cls)
        if status:
            q = q.filter(cls.approval_status == status)
        if category:
            q = q.filter(cls.category == category)
        if group:
            q = q.filter(cls.group == group)
        if plugin_type:
            q = q.filter(cls.type == plugin_type)
        if min_rating is not None:
            q = q.filter(cls.rating >= min_rating)
        if query:
            like = "%{}%".format(query)
            q = q.filter(cls.name.ilike(like) | cls.description.ilike(like) | cls.author.ilike(like))
        total = q.count()
        plugins = q.order_by(cls.rating.desc(), cls.created_at.desc()).offset(offset).limit(limit).all()
        return plugins, total
