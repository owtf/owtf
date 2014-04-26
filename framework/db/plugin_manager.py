from framework.db import models
from sqlalchemy import or_

TEST_GROUPS = ['web', 'net', 'aux']


class PluginDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.PluginDBSession = self.Core.DB.CreateScopedSession(self.Core.Config.FrameworkConfigGetDBPath("PLUGIN_DB_PATH"), models.PluginBase)
        self.LoadWebTestGroups(self.Core.Config.FrameworkConfigGet("WEB_TEST_GROUPS"))
        self.LoadNetTestGroups(self.Core.Config.FrameworkConfigGet("NET_TEST_GROUPS"))
        # After loading the test groups then load the plugins, because of many-to-one relationship
        self.LoadFromFileSystem()  # Load plugins :P

    def GetTestGroupsFromFile(self, file_path):  # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        TestGroups = []
        ConfigFile = open(file_path, 'r').read().splitlines()
        for line in ConfigFile:
            if '#' == line[0]:
                    continue  # Skip comments
            try:
                    Code, Descrip, Hint, URL = line.strip().split(' | ')
            except ValueError:
                    self.Core.Error.FrameworkAbort("Problem in Test Groups file: '" + file_path + "' -> Cannot parse line: " + line)
            if len(Descrip) < 2:
                    Descrip = Hint
            if len(Hint) < 2:
                    Hint = ""
            TestGroups.append({'code': Code, 'descrip': Descrip, 'hint': Hint, 'url': URL})
        return TestGroups

    def LoadWebTestGroups(self, test_groups_file):
        WebTestGroups = self.GetTestGroupsFromFile(test_groups_file)
        session = self.PluginDBSession()
        for group in WebTestGroups:
            session.merge(models.TestGroup(code=group['code'], descrip=group['descrip'], hint=group['hint'], url=group['url'], group="web"))
        session.commit()
        session.close()

    def LoadNetTestGroups(self, test_groups_file):
        NetTestGroups = self.GetTestGroupsFromFile(test_groups_file)
        session = self.PluginDBSession()
        for group in NetTestGroups:
            session.merge(models.TestGroup(code=group['code'], descrip=group['descrip'], hint=group['hint'], url=group['url'], group="net"))
        session.commit()
        session.close()

    def LoadFromFileSystem(self):
        # This commands finds all the plugins and gets their descriptions in one go
        PluginFinderCommand = "for i in $(find " + self.Core.Config.FrameworkConfigGet('PLUGINS_DIR') + " -name '*.py'); do echo \"$i#$(grep ^DESCRIPTION $i|sed 's/ = /=/'|cut -f2 -d=)\"; done | sort"
        session = self.PluginDBSession()
        for line in self.Core.Shell.shell_exec(PluginFinderCommand).split("\n"):
            if not line:
                continue  # Skip blank lines
            Plugin = line.strip().replace(self.Core.Config.FrameworkConfigGet('PLUGINS_DIR'), '')  # Remove plugin directory part of the path
            PluginFile, PluginDescrip = Plugin.split('#')
            PluginDescrip = PluginDescrip[1:-1]  # Get rid of surrounding quotes
            PluginChunks = PluginFile.split('/')
            if (len(PluginChunks) == 3):  # i.e. all modules have a group. i.e. for web plugins: types are -> passive, semi_passive, active, grep
                PluginGroup, PluginType, PluginFile = PluginChunks
            PluginName, PluginCode = PluginFile.split('@')
            PluginCode = PluginCode.split('.')[0]  # Get rid of the ".py"
            session.merge(
                models.Plugin(
                    key=PluginType + '@' + PluginCode,
                    group=PluginGroup,
                    type=PluginType,
                    title=PluginName.title().replace('_', ' '),
                    name=PluginName,
                    code=PluginCode,
                    file=PluginFile,
                    descrip=PluginDescrip
                )
            )
        session.commit()

    def DeriveTestGroupDict(self, obj):
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state")
            return pdict

    def DeriveTestGroupDicts(self, obj_list):
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.DeriveTestGroupDict(obj))
        return dict_list

    def GetTestGroup(self, code):
        session = self.PluginDBSession()
        group = session.query(models.TestGroup).get(code)
        return(self.DeriveTestGroupDict(group))

    def GetAllTestGroups(self):
        session = self.PluginDBSession()
        test_groups = session.query(models.TestGroup).all()
        session.close()
        return(self.DeriveTestGroupDicts(test_groups))

    def GetAllGroups(self):
        session = self.PluginDBSession()
        groups = session.query(models.Plugin.group).distinct().all()
        session.close()
        groups = [i[0] for i in groups]
        return(groups)

    def GetAllTypes(self):
        session = self.PluginDBSession()
        plugin_types = session.query(models.Plugin.type).distinct().all()
        session.close()
        plugin_types = [i[0] for i in plugin_types]  # Necessary because of sqlalchemy
        return(plugin_types)

    def GetTypesForGroup(self, PluginGroup):
        session = self.PluginDBSession()
        plugin_types = session.query(models.Plugin.type).filter_by(group=PluginGroup).distinct().all()
        session.close()
        plugin_types = [i[0] for i in plugin_types]
        return(plugin_types)

    def DerivePluginDict(self, obj):
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state")
            return pdict

    def DerivePluginDicts(self, obj_list):
        plugin_dicts = []
        for obj in obj_list:
            plugin_dicts.append(self.DerivePluginDict(obj))
        return(plugin_dicts)

    def GenerateQueryUsingSession(self, session, criteria):
        query = session.query(models.Plugin)
        if criteria.get("type", None):
            if isinstance(criteria["type"], str) or isinstance(criteria["type"], unicode):
                query = query.filter_by(type=criteria["type"])
            if isinstance(criteria["type"], list):
                query = query.filter(models.Plugin.type.in_(criteria["type"]))
        if criteria.get("group", None):
            if isinstance(criteria["group"], str) or isinstance(criteria["group"], unicode):
                query = query.filter_by(group=criteria["group"])
            if isinstance(criteria["group"], list):
                query = query.filter(models.Plugin.group.in_(criteria["group"]))
        if criteria.get("code", None):
            if isinstance(criteria["code"], str) or isinstance(criteria["code"], unicode):
                query = query.filter_by(code=criteria["code"])
            if isinstance(criteria["code"], list):
                query = query.filter(models.Plugin.code.in_(criteria["code"]))
        if criteria.get("name", None):
            if isinstance(criteria["name"], str) or isinstance(criteria["name"], unicode):
                query = query.filter_by(name=criteria["name"])
            if isinstance(criteria["name"], list):
                query = query.filter(models.Plugin.name.in_(criteria["name"]))
        return query

    def GetAll(self, Criteria={}):
        session = self.PluginDBSession()
        query = self.GenerateQueryUsingSession(session, Criteria)
        plugin_obj_list = query.all()
        return(self.DerivePluginDicts(plugin_obj_list))

    def GetPluginsByType(self, PluginType):
        return(self.GetAll({"plugin_type": PluginType}))

    def GetPluginsByGroup(self, PluginGroup):
        return(self.GetAll({"plugin_group": PluginGroup}))

    def GetPluginsByGroupType(self, PluginGroup, PluginTypeList):
        session = self.PluginDBSession()
        plugins = session.query(models.Plugin).filter(models.Plugin.group == PluginGroup, models.Plugin.type.in_(PluginTypeList)).all()
        session.close()
        return(self.DerivePluginDicts(plugins))

    def GetGroupsForPlugins(self, Plugins):
        session = self.PluginDBSession()
        groups = session.query(models.Plugin.plugin_group).filter(or_(models.Plugin.code.in_(Plugins), models.Plugin.name.in_(Plugins))).distinct().all()
        session.close()
        groups = [i[0] for i in groups]
        return(groups)

# --------------------------------------------------- API Methods ---------------------------------------------------
