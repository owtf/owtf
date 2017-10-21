"""
owtf.db.debug
~~~~~~~~~~~~~

Debug DB stores debug messages
"""

from owtf.dependency_management.dependency_resolver import BaseComponent


class DebugDB(BaseComponent):

    COMPONENT_NAME = "debug_db"

    def __init__(self):
        self.register_in_service_locator()
        self.db = self.get_component("db")

    def add(self, Message):
        """Add a debug message to the DB

        :param Message: Message to be added
        :type Message: `str`
        :return: None
        :rtype: None
        """
        self.db.add('DEBUG_DB', Message)
