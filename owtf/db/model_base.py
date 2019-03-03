"""
owtf.db.model_base
~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_session
from sqlalchemy_mixins import AllFeaturesMixin


class _Model(object):
    """ Custom model mixin with helper methods. """

    @classmethod
    def get(cls, session, **kwargs):
        instance = session.query(cls).filter_by(**kwargs).scalar()
        if instance:
            return instance
        return None

    @classmethod
    def get_or_create(cls, session, **kwargs):
        instance = session.query(cls).filter_by(**kwargs).scalar()
        if instance:
            return instance, False

        instance = cls(**kwargs)
        instance.add(session)

        return instance, True

    def just_created(self):
        pass

    def add(self, session):
        session._add(self)
        self.just_created()
        return self

    def delete(self, session):
        session._delete(self)
        return self


Base = declarative_base(cls=_Model)


class Model(Base, AllFeaturesMixin):
    __abstract__ = True
    pass
