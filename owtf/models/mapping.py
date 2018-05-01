"""
owtf.models.mapping
~~~~~~~~~~~~~~~~~~~

"""
import json

from sqlalchemy import Column, String

from owtf.db.model_base import Model


class Mapping(Model):
    __tablename__ = "mappings"

    owtf_code = Column(String, primary_key=True)
    mappings = Column(String)
    category = Column(String, nullable=True)

    def to_dict(self):
        pdict = dict(self.__dict__)
        pdict.pop("_sa_instance_state", None)
        # If output is present, json decode it
        if pdict.get("mappings", None):
            pdict["mappings"] = json.loads(pdict["mappings"])
        return pdict

    @classmethod
    def get_all(cls, session):
        """Create a mapping between OWTF plugins code and OWTF plugins description.

        :return: Mapping dictionary
            {
                code: [mapped_code, mapped_description],
                code2: [mapped_code, mapped_description],
                ...
            }
        :rtype: dict
        """
        mapping_objs = session.query(Mapping).all()
        obj_dicts = [obj.to_dict() for obj in mapping_objs]
        return {mapping["owtf_code"]: mapping["mappings"] for mapping in obj_dicts}

    @classmethod
    def get_by_code(cls, session, plugin_code):
        """Get the categories for a plugin code

        :param plugin_code: The code for the specific plugin
        :type plugin_code:  `int`
        :return: category for the plugin code
        :rtype: `str`
        """
        category = session.query(Mapping.category).get(plugin_code)
        # Getting the corresponding category back from db
        return category
