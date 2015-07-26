import os
import imp
import json
from framework.db import models
from sqlalchemy import or_
from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import DBPluginInterface
from framework.utils import FileOperations


TEST_GROUPS = ['web', 'net', 'aux']


class PluginDB(BaseComponent, DBPluginInterface):

    COMPONENT_NAME = "db_plugin"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db = self.get_component("db")
        self.timer = self.get_component("timer")
        self.error_handler = self.get_component("error_handler")
        self.LoadWebTestGroups(self.config.FrameworkConfigGet("WEB_TEST_GROUPS"))
        self.LoadNetTestGroups(self.config.FrameworkConfigGet("NET_TEST_GROUPS"))
        # After loading the test groups then load the plugins, because of many-to-one relationship
        self.LoadFromFileSystem()  # Load plugins :P

    def GetTestGroupsFromFile(self, file_path):  # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        TestGroups = []
        ConfigFile = FileOperations.open(file_path, 'r').read().splitlines()
        for line in ConfigFile:
            if '#' == line[0]:
                    continue  # Skip comments
            try:
                    Code, Priority, Descrip, Hint, URL = line.strip().split(' | ')
            except ValueError:
                    self.error_handler.FrameworkAbort("Problem in Test Groups file: '" + file_path + "' -> Cannot parse line: " + line)
            if len(Descrip) < 2:
                    Descrip = Hint
            if len(Hint) < 2:
                    Hint = ""
            TestGroups.append({'code': Code, 'priority': Priority, 'descrip': Descrip, 'hint': Hint, 'url': URL})
        return TestGroups

    def LoadWebTestGroups(self, test_groups_file):
        WebTestGroups = self.GetTestGroupsFromFile(test_groups_file)
        for group in WebTestGroups:
            self.db.session.merge(
                models.TestGroup(
                    code=group['code'],
                    priority=group['priority'],
                    descrip=group['descrip'],
                    hint=group['hint'],
                    url=group['url'],
                    group="web")
                )
        self.db.session.commit()

    def LoadNetTestGroups(self, test_groups_file):
        NetTestGroups = self.GetTestGroupsFromFile(test_groups_file)
        for group in NetTestGroups:
            self.db.session.merge(
                models.TestGroup(
                    code=group['code'],
                    priority=group['priority'],
                    descrip=group['descrip'],
                    hint=group['hint'],
                    url=group['url'],
                    group="net")
                )
        self.db.session.commit()

    def LoadFromFileSystem(self):
        """Loads the plugins from the filesystem and updates their info.

        Walks through each sub-directory of `PLUGINS_DIR`.
        For each file, loads it thanks to the imp module.
        Updates the database with the information for each plugin:
            + 'title': the title of the plugin
            + 'name': the name of the plugin
            + 'code': the internal code of the plugin
            + 'group': the group of the plugin (ex: web)
            + 'type': the type of the plugin (ex: active, passive, ...)
            + 'descrip': the description of the plugin
            + 'file': the filename of the plugin
            + 'internet_res': does the plugin use internet resources?

        """
        # TODO: When the -t, -e or -o is given to OWTF command line, only load
        # the specific plugins (and not all of them like below).
        # Retrieve the list of the plugins (sorted) from the directory given by
        # 'PLUGIN_DIR'.
        plugins = []
        for root, _, files in os.walk(self.config.FrameworkConfigGet('PLUGINS_DIR')):
            plugins.extend([
                os.path.join(root, filename) for filename in files
                if filename.endswith('py')])
        plugins = sorted(plugins)
        # Retrieve the information of the plugin.
        for plugin_path in plugins:
            # Only keep the relative path to the plugin
            plugin = plugin_path.replace(
                self.config.FrameworkConfigGet('PLUGINS_DIR'), '')
            # TODO: Using os.path.sep might not be portable especially on
            # Windows platform since it allows '/' and '\' in the path.
            # Retrieve the group, the type and the file of the plugin.
            chunks = plugin.split(os.path.sep)
            # TODO: Ensure that the variables group, type and file exist when
            # the length of chunks is less than 3.
            if len(chunks) == 3:
                group, type, file = chunks
            # TODO: Add test groups for AUX and then remove the following two lines
            if group == "aux":
                continue
            # Retrieve the internal name and code of the plugin.
            name, code = os.path.splitext(file)[0].split('@')
            # Load the plugin as a module.
            filename, pathname, desc = imp.find_module(
                os.path.splitext(os.path.basename(plugin_path))[0],
                [os.path.dirname(plugin_path)])
            plugin_module = imp.load_module(
                os.path.splitext(file)[0],
                filename,
                pathname,
                desc)
            # Try te retrieve the `attr` dictionary from the module and convert
            # it to json in order to save it into the database.
            attr = None
            try:
                attr = json.dumps(plugin_module.ATTR)
            except AttributeError:  # The plugin didn't define an attr dict.
                pass
            # Save the plugin into the database.
            self.db.session.merge(
                models.Plugin(
                    key=type + '@' + code,
                    group=group,
                    type=type,
                    title=name.title().replace('_', ' '),
                    name=name,
                    code=code,
                    file=file,
                    descrip=plugin_module.DESCRIPTION,
                    attr=attr
                )
            )
        self.db.session.commit()

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
        group = self.db.session.query(models.TestGroup).get(code)
        return(self.DeriveTestGroupDict(group))

    def GetAllTestGroups(self):
        test_groups = self.db.session.query(models.TestGroup).order_by(models.TestGroup.priority.desc()).all()
        return(self.DeriveTestGroupDicts(test_groups))

    def GetAllGroups(self):
        groups = self.db.session.query(models.Plugin.group).distinct().all()
        groups = [i[0] for i in groups]
        return(groups)

    def GetAllTypes(self):
        plugin_types = self.db.session.query(models.Plugin.type).distinct().all()
        plugin_types = [i[0] for i in plugin_types]  # Necessary because of sqlalchemy
        return(plugin_types)

    def GetTypesForGroup(self, PluginGroup):
        plugin_types = self.db.session.query(models.Plugin.type).filter_by(group=PluginGroup).distinct().all()
        plugin_types = [i[0] for i in plugin_types]
        return(plugin_types)

    def DerivePluginDict(self, obj):
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state")
            # REmove outputs array if present
            if "outputs" in pdict.keys():
                pdict.pop("outputs")
            pdict["min_time"] = None
            min_time = obj.min_time
            if min_time is not None:
                pdict["min_time"] = self.timer.get_time_as_str(min_time)
            return pdict

    def DerivePluginDicts(self, obj_list):
        plugin_dicts = []
        for obj in obj_list:
            plugin_dicts.append(self.DerivePluginDict(obj))
        return(plugin_dicts)

    def GenerateQueryUsingSession(self, criteria):
        query = self.db.session.query(models.Plugin).join(models.TestGroup)
        if criteria.get("type", None):
            if isinstance(criteria["type"], (str, unicode)):
                query = query.filter_by(type=criteria["type"])
            if isinstance(criteria["type"], list):
                query = query.filter(models.Plugin.type.in_(criteria["type"]))
        if criteria.get("group", None):
            if isinstance(criteria["group"], (str, unicode)):
                query = query.filter_by(group=criteria["group"])
            if isinstance(criteria["group"], list):
                query = query.filter(models.Plugin.group.in_(criteria["group"]))
        if criteria.get("code", None):
            if isinstance(criteria["code"], (str, unicode)):
                query = query.filter_by(code=criteria["code"])
            if isinstance(criteria["code"], list):
                query = query.filter(models.Plugin.code.in_(criteria["code"]))
        if criteria.get("name", None):
            if isinstance(criteria["name"], (str, unicode)):
                query = query.filter_by(name=criteria["name"])
            if isinstance(criteria["name"], list):
                query = query.filter(models.Plugin.name.in_(criteria["name"]))
        return query.order_by(models.TestGroup.priority.desc())

    def GetAll(self, Criteria={}):
        query = self.GenerateQueryUsingSession(Criteria)
        plugin_obj_list = query.all()
        print(plugin_obj_list[-1])
        return(self.DerivePluginDicts(plugin_obj_list))

    def GetPluginsByType(self, PluginType):
        return(self.GetAll({"type": PluginType}))

    def GetPluginsByGroup(self, PluginGroup):
        return(self.GetAll({"group": PluginGroup}))

    def GetPluginsByGroupType(self, PluginGroup, PluginType):
        return self.GetAll({"type": PluginType, "group": PluginGroup})

    def GetGroupsForPlugins(self, Plugins):
        groups = self.db.session.query(models.Plugin.group).filter(or_(models.Plugin.code.in_(Plugins), models.Plugin.name.in_(Plugins))).distinct().all()
        groups = [i[0] for i in groups]
        return(groups)
