from framework.db import models
from framework.lib.general import cprint
import os

class ResourceDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.ResourceDBSession = self.Core.DB.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("RESOURCE_DB_PATH")), models.ResourceBase)
        self.LoadResourceDBFromFile(self.Core.Config.FrameworkConfigGet("DEFAULT_RESOURCES_PROFILE"))

    def LoadResourceDBFromFile(self, file_path): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        cprint("Loading Resources from: " + file_path + " ..")
        resources = self.GetResourcesFromFile(file_path)
        # resources = [(Type, Name, Resource), (Type, Name, Resource),]
        session = self.ResourceDBSession()
        for Type, Name, Resource in resources:
            # Need more filtering to avoid duplicates
            session.add(models.Resource(resource_type = Type, resource_name = Name, resource = Resource))
        session.commit()
        session.close()

    def GetResourcesFromFile(self, resource_file):
        resources = []
        ConfigFile = open(resource_file, 'r').read().splitlines() # To remove stupid '\n' at the end
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
