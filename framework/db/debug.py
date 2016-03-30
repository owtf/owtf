#!/usr/bin/env python
'''
The DB stores HTTP transactions, unique URLs and more.
'''

from framework.dependency_management.dependency_resolver import BaseComponent


class DebugDB(BaseComponent):
    # Run DB field order:
    COMPONENT_NAME = "debug_db"

    def __init__(self):
        self.register_in_service_locator()
        self.db = self.get_component("db")

    def Add(self, Message):
        self.db.Add('DEBUG_DB', Message)
