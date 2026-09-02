"""
owtf.models.user_plugin
~~~~~~~~~~~~~~~~~~~~~~~

SQLAlchemy model for community-uploaded plugins.
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
        """Public view. Never includes file_path (server-side detail)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "group": self.group,
            "type": self.type,
            "author": self.author,
            "rating": self.rating,
            "approval_status": self.approval_status,
            "version": self.version,
            "tags": self.tags.split(",") if self.tags else [],
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_owner_dict(self):
        """Owner view: public fields plus rejection reason."""
        d = self.to_dict()
        d["rejection_reason"] = self.rejection_reason
        d["user_id"] = self.user_id
        return d

    def to_admin_dict(self):
        """Admin view: owner fields plus reviewer trail and execution_timeout.

        memory_limit is intentionally not exposed: runtime memory limiting is
        out of scope for now, so surfacing it as a knob would be misleading.
        """
        d = self.to_owner_dict()
        d["reviewed_by_user_id"] = self.reviewed_by_user_id
        d["reviewed_at"] = self.reviewed_at.isoformat() if self.reviewed_at else None
        d["execution_timeout"] = self.execution_timeout
        return d

    @classmethod
    def get_for_user(cls, session, user_id):
        return session.query(cls).filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_name(cls, session, name):
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
        is_public=None,
        query=None,
        limit=50,
        offset=0,
    ):
        q = session.query(cls)
        if status:
            q = q.filter(cls.approval_status == status)
        if is_public is not None:
            q = q.filter(cls.is_public.is_(is_public))
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
