"""
owtf.models.test_group
~~~~~~~~~~~~~~~~~~~~~~

"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from owtf.db.model_base import Model


class TestGroup(Model):
    __tablename__ = "test_groups"

    code = Column(String, primary_key=True)
    group = Column(String)  # web, network
    descrip = Column(String)
    hint = Column(String, nullable=True)
    url = Column(String)
    priority = Column(Integer)
    plugins = relationship("Plugin")

    @classmethod
    def get_by_code(cls, session, code):
        """Get the test group based on plugin code

        :param code: Plugin code
        :type code: `str`
        :return: Test group dict
        :rtype: `dict`
        """
        group = session.query(TestGroup).get(code)
        return group.to_dict()

    @classmethod
    def get_all(cls, session):
        """Get all test groups from th DB

        :return:
        :rtype:
        """
        test_groups = session.query(TestGroup).order_by(TestGroup.priority.desc()).all()
        dict_list = []
        for obj in test_groups:
            dict_list.append(obj.to_dict())
        return dict_list
