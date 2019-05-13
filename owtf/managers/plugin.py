"""
owtf.managers.plugin
~~~~~~~~~~~~~~~~~~~~
This module manages the plugins and their dependencies
"""
import imp
import json
import os

from owtf.models.plugin import Plugin
from owtf.models.test_group import TestGroup
from owtf.settings import PLUGINS_DIR
from owtf.utils.error import abort_framework
from owtf.utils.file import FileOperations

TEST_GROUPS = ["web", "network", "auxiliary"]


def get_test_groups_config(file_path):
    """Reads the test groups from a config file

    .. note::
        This needs to be a list instead of a dictionary to preserve order in python < 2.7

    :param file_path: The path to the config file
    :type file_path: `str`
    :return: List of test groups
    :rtype: `list`
    """
    test_groups = []
    config_file = FileOperations.open(file_path, "r").read().splitlines()
    for line in config_file:
        if "#" == line[0]:
            continue  # Skip comments
        try:
            code, priority, descrip, hint, url = line.strip().split(" | ")
        except ValueError:
            abort_framework(
                "Problem in Test Groups file: '{!s}' -> Cannot parse line: {!s}".format(
                    file_path, line
                )
            )
        if len(descrip) < 2:
            descrip = hint
        if len(hint) < 2:
            hint = ""
        test_groups.append(
            {
                "code": code,
                "priority": priority,
                "descrip": descrip,
                "hint": hint,
                "url": url,
            }
        )
    return test_groups


def load_test_groups(session, file_default, file_fallback, plugin_group):
    """Load test groups into the DB.

    :param test_groups_file: The path to the test groups config
    :type test_groups_file: `str`
    :param plugin_group: Plugin group to load
    :type plugin_group: `str`
    :return: None
    :rtype: None
    """
    file_path = file_default
    if not os.path.isfile(file_default):
        file_path = file_fallback
    test_groups = get_test_groups_config(file_path)
    for group in test_groups:
        session.merge(
            TestGroup(
                code=group["code"],
                priority=group["priority"],
                descrip=group["descrip"],
                hint=group["hint"],
                url=group["url"],
                group=plugin_group,
            )
        )
    session.commit()


def load_plugins(session):
    """Loads the plugins from the filesystem and updates their info.

    .. note::
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
    for root, _, files in os.walk(PLUGINS_DIR):
        plugins.extend(
            [
                os.path.join(root, filename)
                for filename in files
                if filename.endswith("py")
            ]
        )
    plugins = sorted(plugins)
    # Retrieve the information of the plugin.
    for plugin_path in plugins:
        # Only keep the relative path to the plugin
        plugin = plugin_path.replace(PLUGINS_DIR, "")
        # TODO: Using os.path.sep might not be portable especially on
        # Windows platform since it allows '/' and '\' in the path.
        # Retrieve the group, the type and the file of the plugin.
        # Ensure all empty strings are removed from the list
        chunks = list(filter(None, plugin.split(os.path.sep)))
        # TODO: Ensure that the variables group, type and file exist when
        # the length of chunks is less than 3.
        if len(chunks) == 3:
            group, type, file = chunks
        # Retrieve the internal name and code of the plugin.
        name, code = os.path.splitext(file)[0].split("@")
        # Only load the plugin if in XXX_TEST_GROUPS configuration (e.g. web_testgroups.cfg)
        if session.query(TestGroup).get(code) is None:
            continue
        # Load the plugin as a module.
        filename, pathname, desc = imp.find_module(
            os.path.splitext(os.path.basename(plugin_path))[0],
            [os.path.dirname(plugin_path)],
        )
        plugin_module = imp.load_module(
            os.path.splitext(file)[0], filename, pathname, desc
        )
        # Try te retrieve the `attr` dictionary from the module and convert
        # it to json in order to save it into the database.
        attr = None
        try:
            attr = json.dumps(plugin_module.ATTR)
        except AttributeError:  # The plugin didn't define an attr dict.
            pass
        # Save the plugin into the database.
        session.merge(
            Plugin(
                key="{!s}@{!s}".format(type, code),
                group=group,
                type=type,
                title=name.title().replace("_", " "),
                name=name,
                code=code,
                file=file,
                descrip=plugin_module.DESCRIPTION,
                attr=attr,
            )
        )
    session.commit()


def get_types_for_plugin_group(session, plugin_group):
    """Get available plugin types for a plugin group

    :param plugin_group: Plugin group
    :type plugin_group: `str`
    :return: List of available plugin types
    :rtype: `list`
    """
    plugin_types = session.query(Plugin.type).filter_by(
        group=plugin_group
    ).distinct().all()
    plugin_types = [i[0] for i in plugin_types]
    return plugin_types


def plugin_gen_query(session, criteria):
    """Generate a SQLAlchemy query based on the filter criteria
    :param criteria: Filter criteria
    :type criteria: `dict`
    :return:
    :rtype:
    """
    query = session.query(Plugin).join(TestGroup)
    if criteria.get("type", None):
        if isinstance(criteria["type"], str):
            query = query.filter(Plugin.type == criteria["type"])
        if isinstance(criteria["type"], list):
            query = query.filter(Plugin.type.in_(criteria["type"]))
    if criteria.get("group", None):
        if isinstance(criteria["group"], str):
            query = query.filter(Plugin.group == criteria["group"])
        if isinstance(criteria["group"], list):
            query = query.filter(Plugin.group.in_(criteria["group"]))
    if criteria.get("code", None):
        if isinstance(criteria["code"], str):
            query = query.filter(Plugin.code == criteria["code"])
        if isinstance(criteria["code"], list):
            query = query.filter(Plugin.code.in_(criteria["code"]))
    if criteria.get("name", None):
        if isinstance(criteria["name"], str):
            query = query.filter(Plugin.name == criteria["name"])
        if isinstance(criteria["name"], list):
            query = query.filter(Plugin.name.in_(criteria["name"]))
    return query.order_by(TestGroup.priority.desc())


def get_all_plugin_dicts(session, criteria=None):
    """Get plugin dicts based on filter criteria

    :param criteria: Filter criteria
    :type criteria: `dict`
    :return: List of plugin dicts
    :rtype: `list`
    """
    if criteria is None:
        criteria = {}
    if "code" in criteria:
        criteria["code"] = Plugin.name_to_code(session, criteria["code"])
    query = plugin_gen_query(session, criteria)
    plugin_obj_list = query.all()
    plugin_dicts = []
    for obj in plugin_obj_list:
        plugin_dicts.append(obj.to_dict())
    return plugin_dicts


def get_plugins_by_type(session, plugin_type):
    """Get plugins based on type argument

    :param plugin_type: Plugin type
    :type plugin_type: `str`
    :return: List of plugin dicts
    :rtype: `list`
    """
    return get_all_plugin_dicts(session, {"type": plugin_type})


def get_plugins_by_group(session, plugin_group):
    """Get plugins by plugin group

    :param plugin_group: Plugin group
    :type plugin_group: `str`
    :return: List of plugin dicts
    :rtype: `list`
    """
    return get_all_plugin_dicts(session, {"group": plugin_group})


def get_plugins_by_group_type(session, plugin_group, plugin_type):
    """Get plugins by group and plugin type

    :param plugin_group: Plugin group
    :type plugin_group: `str`
    :param plugin_type: plugin type
    :type plugin_type: `str`
    :return: List of plugin dicts
    :rtype: `list`
    """
    return get_all_plugin_dicts(session, {"type": plugin_type, "group": plugin_group})
