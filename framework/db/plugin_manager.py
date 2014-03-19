from framework.db import models
import os

TEST_GROUPS = ['web', 'net']

class PluginDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.PluginDBSession = self.Core.DB.CreateScopedSession(os.path.expanduser(self.Core.Config.FrameworkConfigGet("PLUGIN_DB_PATH")), models.PluginBase)
        self.LoadWebTestGroups(self.Core.Config.FrameworkConfigGet("WEB_TEST_GROUPS"))
        self.LoadNetTestGroups(self.Core.Config.FrameworkConfigGet("NET_TEST_GROUPS"))
        # After loading the test groups then load the plugins, because of many-to-one relationship
        self.LoadFromFileSystem() # Load plugins :P

    def GetTestGroupsFromFile(self, file_path): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        TestGroups = []
        ConfigFile = open(file_path, 'r').read().splitlines()
        for line in ConfigFile:
            if '#' == line[0]:
                    continue # Skip comments
            try:
                    Code, Descrip, Hint, URL = line.strip().split(' | ')
            except ValueError:
                    self.Core.Error.FrameworkAbort("Problem in Test Groups file: '"+ file_path +"' -> Cannot parse line: "+line)
            if len(Descrip) < 2:
                    Descrip = Hint
            if len(Hint) < 2:
                    Hint = ""
            TestGroups.append({ 'Code' : Code, 'Descrip' : Descrip, 'Hint' : Hint, 'URL' : URL })
        return TestGroups

    def LoadWebTestGroups(self, test_groups_file):
        WebTestGroups = self.GetTestGroupsFromFile(test_groups_file)
        session = self.PluginDBSession()
        for group in WebTestGroups:
            session.merge(models.TestCode(code = group['Code'], descrip = group['Descrip'], hint = group['Hint'], url = group['URL'], group = "web"))
        session.commit()
        session.close()

    def LoadNetTestGroups(self, test_groups_file):
        NetTestGroups = self.GetTestGroupsFromFile(test_groups_file)
        session = self.PluginDBSession()
        for group in NetTestGroups:
            session.merge(models.TestCode(code = group['Code'], descrip = group['Descrip'], hint = group['Hint'], url = group['URL'], group = "net"))
        session.commit()
        session.close()

    def LoadFromFileSystem(self):
        # This commands finds all the plugins and gets their descriptions in one go
        PluginFinderCommand = "for i in $(find "+self.Core.Config.FrameworkConfigGet('PLUGINS_DIR')+" -name '*.py'); do echo \"$i#$(grep ^DESCRIPTION $i|sed 's/ = /=/'|cut -f2 -d=)\"; done | sort"
        session = self.PluginDBSession()
        for line in self.Core.Shell.shell_exec(PluginFinderCommand).split("\n"):
            if not line:
                continue # Skip blank lines
            Plugin = line.strip().replace(self.Core.Config.FrameworkConfigGet('PLUGINS_DIR'), '') # Remove plugin directory part of the path
            PluginFile, PluginDescrip = Plugin.split('#')
            PluginDescrip = PluginDescrip[1:-1] # Get rid of surrounding quotes
            PluginChunks = PluginFile.split('/')
            if (len(PluginChunks) == 3): # i.e. all modules have a group. i.e. for web plugins: types are -> passive, semi_passive, active, grep
                PluginGroup, PluginType, PluginFile = PluginChunks
            PluginName, PluginCode = PluginFile.split('@')
            PluginCode = PluginCode.split('.')[0] # Get rid of the ".py"
            session.merge(models.Plugin(
                                            key = PluginType + '@' + PluginCode,
                                            plugin_group = PluginGroup,
                                            plugin_type = PluginType,
                                            plugin_title = PluginName.title().replace('_', ' '),
                                            plugin_name = PluginName,
                                            plugin_code = PluginCode,
                                            plugin_file = PluginFile,
                                            plugin_descrip = PluginDescrip
                                        ))
        session.commit()

    def GetTestCode(self, code):
        session = self.PluginDBSession()
        group = session.query(models.TestGroup).get(code)
        if group:
            return({'Code': group.code, 'Descrip': group.descrip, 'Hint': group.hint, 'URL': group.url})
        return group

    def GetAllGroups(self):
        session = self.PluginDBSession()
        groups = session.query(models.Plugin.plugin_group).distinct().all()
        session.close()
        groups = [i[0] for i in groups]
        return(groups)

    def GetAllTypes(self):
        session = self.PluginDBSession()
        plugin_types = session.query(models.Plugin.plugin_type).distinct().all()
        session.close()
        plugin_types = [i[0] for i in plugin_types] # Necessary because of sqlalchemy
        return(plugin_types)

    def GetTypesForGroup(self, PluginGroup):
        session = self.PluginDBSession()
        plugin_types = session.query(models.Plugin.plugin_type).filter_by(plugin_group = PluginGroup).distinct().all()
        session.close()
        plugin_types = [i[0] for i in plugin_types]
        return(plugin_types)

    def GetPluginDictFromModel(self, obj):
        return({"Group" : obj.plugin_group,
                "Type" : obj.plugin_type,
                "File" : obj.plugin_file,
                "Code" : obj.plugin_code,
                "Name" : obj.plugin_name,
                "Title": obj.plugin_title,
                "Descrip": obj.plugin_descrip
                })

    def GetPluginDictsFromModels(self, obj_list):
        plugin_dicts = []
        for obj in obj_list:
            plugin_dicts.append(self.GetPluginDictFromModel(obj))
        return(plugin_dicts)

    def GetPluginsByType(self, PluginType):
        session = self.PluginDBSession()
        plugins = session.query(models.Plugin).filter_by(plugin_type = PluginType).all()
        session.close()
        return(self.GetPluginDictsFromModels(plugins))

    def GetPluginsByGroup(self, PluginGroup):
        session = self.PluginDBSession()
        plugins = session.query(models.Plugin).filter_by(plugin_group = PluginGroup).all()
        session.close()
        return(self.GetPluginDictsFromModels(plugins))
