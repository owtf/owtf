"""
owtf.db.plugin_manager

This module manages the plugins and their dependencies
"""

import os
import imp
import json

from sqlalchemy import or_

from owtf.db import models
from owtf.dependency_management.dependency_resolver import BaseComponent
from owtf.dependency_management.interfaces import DBPluginInterface
from owtf.utils import FileOperations


TEST_GROUPS = ['web', 'network', 'auxiliary']


class PluginDB(BaseComponent, DBPluginInterface):

    COMPONENT_NAME = "db_plugin"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.db = self.get_component("db")
        self.error_handler = self.get_component("error_handler")
        self.load_test_groups(self.config.select_user_or_default_config_path(
            self.config.get_val("WEB_TEST_GROUPS"), self.config.get_val("WEB_PLUGIN_CONFIG_DIR")),
            "web")
        self.load_test_groups(self.config.select_user_or_default_config_path(
            self.config.get_val("NET_TEST_GROUPS"), self.config.get_val("NET_PLUGIN_CONFIG_DIR")),
            "network")
        self.load_test_groups(self.config.select_user_or_default_config_path(
            self.config.get_val("AUX_TEST_GROUPS"), self.config.get_val("AUX_PLUGIN_CONFIG_DIR")),
            "auxiliary")
        # After loading the test groups then load the plugins, because of many-to-one relationship
        self.load_plugins()  # Load plugins :P

    def init(self):
        self.timer = self.get_component("timer")

    def get_test_groups_config(self, file_path):
        """Reads the test groups from a config file

        .note::
            This needs to be a list instead of a dictionary to preserve order in python < 2.7

        :param file_path: The path to the config file
        :type file_path: `str`
        :return: List of test groups
        :rtype: `list`
        """
        test_groups = []
        config_file = FileOperations.open(file_path, 'r').read().splitlines()
        for line in config_file:
            if '#' == line[0]:
                continue  # Skip comments
            try:
                code, priority, descrip, hint, url = line.strip().split(' | ')
            except ValueError:
                self.error_handler.abort_framework("Problem in Test Groups file: '%s' -> Cannot parse line: %s" %
                                                   (file_path, line))
            if len(descrip) < 2:
                descrip = hint
            if len(hint) < 2:
                hint = ""
            test_groups.append({'code': code, 'priority': priority, 'descrip': descrip, 'hint': hint, 'url': url})
        return test_groups

    def load_test_groups(self, test_groups_file, plugin_group):
        """Load test groups into the DB.

        :param test_groups_file: The path to the test groups config
        :type test_groups_file: `str`
        :param plugin_group: Plugin group to load
        :type plugin_group: `str`
        :return: None
        :rtype: None
        """
        test_groups = self.get_test_groups_config(test_groups_file)
        for group in test_groups:
            self.db.session.merge(
                models.TestGroup(
                    code=group['code'],
                    priority=group['priority'],
                    descrip=group['descrip'],
                    hint=group['hint'],
                    url=group['url'],
                    group=plugin_group)
            )
        self.db.session.commit()

    def load_plugins(self):
        """Loads the plugins from the filesystem and updates their info.

        .note::
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

        :return: None
        :rtype: None
        """
        # TODO: When the -t, -e or -o is given to OWTF command line, only load
        # the specific plugins (and not all of them like below).
        # Retrieve the list of the plugins (sorted) from the directory given by
        # 'PLUGIN_DIR'.
        plugins = []
        for root, _, files in os.walk(self.config.get_val('PLUGINS_DIR')):
            plugins.extend([os.path.join(root, filename) for filename in files if filename.endswith('py')])
        plugins = sorted(plugins)
        # Retrieve the information of the plugin.
        for plugin_path in plugins:
            # Only keep the relative path to the plugin
            plugin = plugin_path.replace(self.config.get_val('PLUGINS_DIR'), '')
            # TODO: Using os.path.sep might not be portable especially on
            # Windows platform since it allows '/' and '\' in the path.
            # Retrieve the group, the type and the file of the plugin.
            chunks = plugin.split(os.path.sep)
            # TODO: Ensure that the variables group, type and file exist when
            # the length of chunks is less than 3.
            if len(chunks) == 3:
                group, type, file = chunks
            # Retrieve the internal name and code of the plugin.
            name, code = os.path.splitext(file)[0].split('@')
            # Only load the plugin if in XXX_TEST_GROUPS configuration (e.g. web_testgroups.cfg)
            if self.db.session.query(models.TestGroup).get(code) is None:
                continue
            # Load the plugin as a module.
            filename, pathname, desc = imp.find_module(os.path.splitext(os.path.basename(plugin_path))[0],
                                                       [os.path.dirname(plugin_path)])
            plugin_module = imp.load_module(os.path.splitext(file)[0], filename, pathname, desc)
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
                    key='%s@%s' % (type, code),
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

    def derive_test_group_dict(self, obj):
        """Fetch the test group dict from the obj

        :param obj: The test group object
        :type obj:
        :return: Test group dict
        :rtype: `dict`
        """
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state")
            return pdict

    def derive_test_group_dicts(self, obj_list):
        """Fetch the test group dicts from the obj list

        :param obj_list: The test group object list
        :type obj_list: `list`
        :return: Test group dicts in a list
        :rtype: `list`
        """
        dict_list = []
        for obj in obj_list:
            dict_list.append(self.derive_test_group_dict(obj))
        return dict_list

    def get_test_group(self, code):
        """Get the test group based on plugin code

        :param code: Plugin code
        :type code: `str`
        :return: Test group dict
        :rtype: `dict`
        """
        group = self.db.session.query(models.TestGroup).get(code)
        return self.derive_test_group_dict(group)

    def get_all_test_groups(self):
        """Get all test groups from th DB

        :return:
        :rtype:
        """
        test_groups = self.db.session.query(models.TestGroup).order_by(models.TestGroup.priority.desc()).all()
        return self.derive_test_group_dicts(test_groups)

    def get_all_plugin_groups(self):
        """Get all plugin groups from the DB

        :return: List of available plugin groups
        :rtype: `list`
        """
        groups = self.db.session.query(models.Plugin.group).distinct().all()
        groups = [i[0] for i in groups]
        return groups

    def get_all_plugin_types(self):
        """Get all plugin types from the DB

        :return: All available plugin types
        :rtype: `list`
        """
        plugin_types = self.db.session.query(models.Plugin.type).distinct().all()
        plugin_types = [i[0] for i in plugin_types]  # Necessary because of sqlalchemy
        return plugin_types

    def get_types_for_plugin_group(self, plugin_group):
        """Get available plugin types for a plugin group

        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :return: List of available plugin types
        :rtype: `list`
        """
        plugin_types = self.db.session.query(models.Plugin.type).filter_by(group=plugin_group).distinct().all()
        plugin_types = [i[0] for i in plugin_types]
        return plugin_types

    def derive_plugin_dict(self, obj):
        """Fetch the plugin dict from an object

        :param obj: Plugin object
        :type obj:
        :return: Plugin dict
        :rtype: `dict`
        """
        if obj:
            pdict = dict(obj.__dict__)
            pdict.pop("_sa_instance_state")
            # Remove outputs array if present
            if "outputs" in list(pdict.keys()):
                pdict.pop("outputs")
            pdict["min_time"] = None
            min_time = obj.min_time
            if min_time is not None:
                pdict["min_time"] = self.timer.get_time_as_str(min_time)
            return pdict

    def derive_plugin_dicts(self, obj_list):
        """Fetch plugin dicts from a obj list

        :param obj_list: List of plugin objects
        :type obj_list: `list`
        :return: List of plugin dicts
        :rtype: `list`
        """
        plugin_dicts = []
        for obj in obj_list:
            plugin_dicts.append(self.derive_plugin_dict(obj))
        return plugin_dicts

    def gen_query(self, criteria):
        """Generate a SQLAlchemy query based on the filter criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :return:
        :rtype:
        """
        query = self.db.session.query(models.Plugin).join(models.TestGroup)
        if criteria.get("type", None):
            if isinstance(criteria["type"], str):
                query = query.filter(models.Plugin.type == criteria["type"])
            if isinstance(criteria["type"], list):
                query = query.filter(models.Plugin.type.in_(criteria["type"]))
        if criteria.get("group", None):
            if isinstance(criteria["group"], str):
                query = query.filter_by(group=criteria["group"])
            if isinstance(criteria["group"], list):
                query = query.filter(models.Plugin.group.in_(criteria["group"]))
        if criteria.get("code", None):
            if isinstance(criteria["code"], str):
                query = query.filter_by(code=criteria["code"])
            if isinstance(criteria["code"], list):
                query = query.filter(models.Plugin.code.in_(criteria["code"]))
        if criteria.get("name", None):
            if isinstance(criteria["name"], str):
                query = query.filter(models.Plugin.name == criteria["name"])
            if isinstance(criteria["name"], list):
                query = query.filter(models.Plugin.name.in_(criteria["name"]))
        return query.order_by(models.TestGroup.priority.desc())

    def plugin_name_to_code(self, codes):
        """Given list of names, get the corresponding codes

        :param codes: The codes to fetch
        :type codes: `list`
        :return: Corresponding plugin codes as a list
        :rtype: `list`
        """
        checklist = ["OWTF-", "PTES-", "FCUS-"]
        query = self.db.session.query(models.Plugin.code)
        for count, name in enumerate(codes):
            if all(check not in name for check in checklist):
                code = query.filter(models.Plugin.name == name).first()
                codes[count] = str(code[0])
        return codes

    def get_all(self, criteria=None):
        """Get plugin dicts based on filter criteria

        :param criteria: Filter criteria
        :type criteria: `dict`
        :return: List of plugin dicts
        :rtype: `list`
        """
        if criteria is None:
            criteria = dict()

        if "code" in criteria:
            criteria["code"] = self.plugin_name_to_code(criteria["code"])
        query = self.gen_query(criteria)
        plugin_obj_list = query.all()
        return self.derive_plugin_dicts(plugin_obj_list)

    def get_plugins_by_type(self, plugin_type):
        """Get plugins based on type argument

        :param plugin_type: Plugin type
        :type plugin_type: `str`
        :return: List of plugin dicts
        :rtype: `list`
        """
        return self.get_all({"type": plugin_type})

    def get_plugins_by_group(self, plugin_group):
        """Get plugins by plugin group

        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :return: List of plugin dicts
        :rtype: `list`
        """
        return self.get_all({"group": plugin_group})

    def get_plugins_by_group_type(self, plugin_group, plugin_type):
        """Get plugins by group and plugin type

        :param plugin_group: Plugin group
        :type plugin_group: `str`
        :param plugin_type: plugin type
        :type plugin_type: `str`
        :return: List of plugin dicts
        :rtype: `list`
        """
        return self.get_all({"type": plugin_type, "group": plugin_group})

    def get_groups_for_plugins(self, plugins):
        """Gets available groups for selected plugins

        :param plugins: Plugins selected
        :type plugins: `list`
        :return: List of available plugin groups
        :rtype: `list`
        """
        groups = self.db.session.query(models.Plugin.group).filter(or_(models.Plugin.code.in_(plugins),
            models.Plugin.name.in_(plugins))).distinct().all()
        groups = [i[0] for i in groups]
        return groups
