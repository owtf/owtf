from framework.db import models
from framework.config import config
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.lib.general import cprint
import os

class ResourceDB(BaseComponent):

    COMPONENT_NAME = "resource"

    def __init__(self, Core):
        self.register_in_service_locator()
        self.Core = Core
        self.config = self.Core.Config
        self.db_config = self.Core.DB.Config
        self.target = self.Core.DB.Target
        self.db = self.Core.DB
        self.ResourceDBSession = self.db.CreateScopedSession(self.config.FrameworkConfigGetDBPath("RESOURCE_DB_PATH"), models.ResourceBase)
        self.LoadResourceDBFromFile(self.config.FrameworkConfigGet("DEFAULT_RESOURCES_PROFILE"))

    def LoadResourceDBFromFile(self, file_path): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        cprint("Loading Resources from: " + file_path + " ..")
        resources = self.GetResourcesFromFile(file_path)
        # resources = [(Type, Name, Resource), (Type, Name, Resource),]
        session = self.ResourceDBSession()
        for Type, Name, Resource in resources:
            # Need more filtering to avoid duplicates
            if not session.query(models.Resource).filter_by(resource_type = Type, resource_name = Name, resource = Resource).all():
                session.add(models.Resource(resource_type = Type, resource_name = Name, resource = Resource))
        session.commit()
        session.close()

    def GetResourcesFromFile(self, resource_file):
        resources = []
        ConfigFile = self.Core.open(resource_file, 'r').read().splitlines() # To remove stupid '\n' at the end
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comment lines
            try:
                Type, Name, Resource = line.split('_____')
                # Resource = Resource.strip()
                resources.append((Type, Name, Resource))
            except ValueError:
                cprint("ERROR: The delimiter is incorrect in this line at Resource File: "+str(line.split('_____')))
        return resources

    def GetReplacementDict(self):
        configuration = self.db_config.GetReplacementDict()
        configuration.update(self.target.GetTargetConfig())
        configuration.update(self.config.GetReplacementDict())
        return configuration

    def GetRawResources(self, ResourceType):
        session = self.ResourceDBSession()
        filter_query = session.query(models.Resource.resource_name, models.Resource.resource).filter_by(resource_type = ResourceType)
        # Sorting is necessary for working of ExtractURLs, since it must run after main command, so order is imp
        sort_query = filter_query.order_by(models.Resource.id)
        raw_resources = sort_query.all()
        session.close()
        return raw_resources

    def GetResources(self, ResourceType):
        replacement_dict = self.GetReplacementDict()
        raw_resources = self.GetRawResources(ResourceType)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.config.MultipleReplace(resource, replacement_dict)])
        return resources

    def GetRawResourceList(self, ResourceList):
        session = self.ResourceDBSession()
        raw_resources = session.query(models.Resource.resource_name, models.Resource.resource).filter(models.Resource.resource_type.in_(ResourceList)).all()
        session.close()
        return raw_resources

    def GetResourceList(self, ResourceTypeList):
        replacement_dict = self.GetReplacementDict()
        raw_resources = self.GetRawResourceList(ResourceTypeList)
        resources = []
        for name, resource in raw_resources:
            resources.append([name, self.config.MultipleReplace(resource, replacement_dict)])
        return resources

