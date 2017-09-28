"""
owtf.db.target_manager
~~~~~~~~~~~~~~~~~~~~~~

"""

import os
import datetime
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from owtf.dependency_management.dependency_resolver import BaseComponent, ServiceLocator
from owtf.dependency_management.interfaces import TargetInterface
from owtf.lib.exceptions import DBIntegrityException, InvalidTargetReference, InvalidParameterType
from owtf.db import models
from owtf.managers.session import session_required
from owtf.lib.general import cprint  # TODO: Shift to logging


TARGET_CONFIG = {
    'id': 0,
    'target_url': '',
    'host_name': '',
    'host_path': '',
    'url_scheme': '',
    'port_number': '',  # In str form
    'host_ip': '',
    'alternative_ips': '',  # str(list), so it can easily reversed using list(str)
    'ip_url': '',
    'top_domain': '',
    'top_url': '',
    'scope': True,
    "max_user_rank": -1,
    "max_owtf_rank": -1
}

PATH_CONFIG = {
    'partial_url_output_path': '',
    'host_output': '',
    'port_output': '',
    'url_output': '',
    'plugin_output_dir': ''
}


def target_required(func):
    """
    In order to use this decorator on a `method` there are two requirements
    + target_id must be a kwarg of the function
    + Core must be attached to the object at self.Core

    All this decorator does is check if a valid value is passed for target_id
    if not get the target_id from target manager and pass it
    """
    def wrapped_function(*args, **kwargs):
        if "target_id" not in kwargs:
            kwargs["target_id"] = ServiceLocator.get_component("target").get_target_id()
        return func(*args, **kwargs)
    return wrapped_function


class TargetDB(BaseComponent, TargetInterface):
    # All these variables reflect to current target which is referenced by a unique ID
    target_id = None
    target_config = dict(TARGET_CONFIG)
    path_config = dict(PATH_CONFIG)

    COMPONENT_NAME = "target"

    def __init__(self):
        self.register_in_service_locator()
        self.config = self.get_component("config")
        self.command_register = self.get_component("command_register")
        self.db = self.get_component("db")

    def set_target(self, target_id):
        """Set a target by ID

        :param target_id: target ID
        :type target_id: `int`
        :return: None
        :rtype: None
        """
        try:
            self.target_id = target_id
            self.target_config = self.get_target_config_by_id(target_id)
            self.path_config = self.get_path_configs(self.target_config)
        except InvalidTargetReference:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(target_id))

    def get_path_configs(self, target_config):
        """Get paths to output directories

        :param target_config: Target config
        :type target_config: `dict`
        :return: Path config
        :rtype: `dict`
        """
        path_config = {}
        # Set the output directory.
        path_config['host_output'] = os.path.join(self.config.get_val('OUTPUT_PATH'),
                                                  target_config['host_ip'])
        path_config['port_output'] = os.path.join(path_config['host_output'], target_config['port_number'])
        # Set the URL output directory (plugins will save their data here).
        path_config['url_output'] = os.path.join(self.config.get_target_dir(target_config['target_url']))
        # Set the partial results path.
        path_config['partial_url_output_path'] = os.path.join(path_config['url_output'], 'partial')
        return path_config

    def get_target_id(self):
        """Return target ID

        :return: target ID
        :rtype: `int`
        """
        return self.target_id

    def get_target_url(self):
        """Return target URL

        :return: Target URL
        :rtype: `str`
        """
        return self.get("target_url")

    def get_target_urls(self):
        """Return target URLs

        :return: List of target urls
        :rtype: `list`
        """
        return self.get_all("target_url")

    def get_indexed_targets(self):
        """Get indexed targets

        :return:
        :rtype:
        """
        results = self.db.session.query(models.Target.id, models.Target.target_url).all()
        return results

    def get_target_config(self):
        """Return target config

        :return: Target config
        :rtype: `dict`
        """
        return self.target_config

    def get_path_config(self):
        """Return path config

        :return: Path config
        :rtype: `dict`
        """
        return self.path_config

    def get_path(self, output_type):
        return self.path_config.get(output_type, None)

    def set_path(self, output_type, path):
        # Mainly used for setting output paths for individual plugins, which
        # need not be saved: plugin_output_dir.
        self.path_config[output_type] = path

    @session_required
    def add_target(self, target_url, session_id=None):
        """Adds a target to session

        :param target_url: Target url
        :type target_url: `str`
        :param session_id: session ID
        :type session_id: `int`
        :return: None
        :rtype: None
        """
        if target_url not in self.get_target_urls():
            # A try-except can be used here, but then ip-resolution takes time
            # even if target is present
            target_config = self.config.derive_config_from_url(target_url)
            config_obj = models.Target(target_url=target_url)
            config_obj.host_name = target_config["host_name"]
            config_obj.host_path = target_config["host_path"]
            config_obj.url_scheme = target_config["url_scheme"]
            config_obj.port_number = target_config["port_number"]
            config_obj.host_ip = target_config["host_ip"]
            config_obj.alternative_ips = str(target_config["alternative_ips"])
            config_obj.ip_url = target_config["ip_url"]
            config_obj.top_domain = target_config["top_domain"]
            config_obj.top_url = target_config["top_url"]
            self.db.session.add(config_obj)
            config_obj.sessions.append(self.db.session.query(models.Session).get(session_id))
            self.db.session.commit()
            target_id = config_obj.id
            self.create_missing_dirs_target(target_url)
            self.set_target(target_id)
        else:
            session_obj = self.db.session.query(models.Session).get(session_id)
            target_obj = self.db.session.query(models.Target).filter_by(target_url=target_url).one()
            if session_obj in target_obj.sessions:
                raise DBIntegrityException("%s already present in Target DB & session" % target_url)
            else:
                self.db.OWTFSession.add_target_to_session(target_obj.id, session_id=session_obj.id)

    @session_required
    def add_targets(self, target_urls, session_id=None):
        """Add multiple targets

        :param target_urls: List of target urls
        :type target_urls: `list`
        :param session_id: session ID
        :type session_id: `int`
        :return: None
        :rtype: None
        """
        for target_url in target_urls:
            self.add_target(target_url, session_id=session_id)

    def update_target(self, data_dict, target_url=None, id=None):
        """Update a target in the DB

        :param data_dict: Modified data
        :type data_dict: `dict`
        :param target_url: Target url
        :type target_url: `str`
        :param id: Target ID
        :type id: `int`
        :return: None
        :rtype: None
        """
        target_obj = None
        if id:
            target_obj = self.db.session.query(models.Target).get(id)
        if target_url:
            target_obj = self.db.session.query(models.Target).filter_by(target_url=target_url).one()
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(id) if id else str(target_url))
        # TODO: Updating all related attributes when one attribute is changed
        if data_dict.get("scope", None) is not None:
            target_obj.scope = self.config.ConvertStrToBool(data_dict.get("scope", None))
        self.db.session.commit()

    def delete_target(self, target_url=None, id=None):
        """Delete a target from DB

        :param target_url: target URL
        :type target_url: `str`
        :param id: Target ID
        :type id: `int`
        :return: None
        :rtype: None
        """
        if id:
            target_obj = self.db.session.query(models.Target).get(id)
        if target_url:
            target_obj = self.db.session.query(models.Target).filter_by(target_url=target_url).one()
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(id) if id else str(target_url))
        target_url = target_obj.target_url
        self.db.session.delete(target_obj)
        self.db.session.commit()
        self.config.cleanup_target_dirs(target_url)

    def create_missing_dirs_target(self, target_url):
        """Creates missing output dirs for target

        :param target_url: Target URL
        :type target_url: `str`
        :return: None
        :rtype: None
        """
        self.config.create_output_dir_target(target_url)

    def get_target_url_for_id(self, id):
        """Get target URL by target ID

        :param id: target ID
        :type id: `int`
        :return: Target url
        :rtype: `str`
        """
        target_obj = self.db.session.query(models.Target).get(id)
        if not target_obj:
            cprint("Failing with ID: %s" % str(id))
            raise InvalidTargetReference("Target doesn't exist with ID: %s" % str(id))
        return target_obj.target_url

    def get_target_config_by_id(self, id):
        """Get target config by id

        :param id: Target id
        :type id: `int`
        :return: Config dict
        :rtype: `dict`
        """
        target_obj = self.db.session.query(models.Target).get(id)
        if not target_obj:
            raise InvalidTargetReference("Target doesn't exist: %s" % str(id))
        return self.get_target_config_dict(target_obj)

    def _generate_query(self, filter_data, session_id, for_stats=False):
        """Generate query

        :param filter_data: Filter data
        :type filter_data: `dict`
        :param session_id: session ID
        :type session_id: `int`
        :param for_stats: true/false
        :type for_stats: `bool`
        :return:
        :rtype:
        """
        query = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id))
        if filter_data.get("search") is not None:
            if filter_data.get('target_url', None):
                if isinstance(filter_data.get('target_url'), list):
                    filter_data['target_url'] = filter_data['target_url'][0]
                query = query.filter(models.Target.target_url.like("%%%s%%" % filter_data['target_url']))
        else:
            if filter_data.get("target_url", None):
                if isinstance(filter_data["target_url"], str):
                    query = query.filter_by(target_url=filter_data["target_url"])
                if isinstance(filter_data["target_url"], list):
                    query = query.filter(models.Target.target_url.in_(filter_data.get("target_url")))
            if filter_data.get("host_ip", None):
                if isinstance(filter_data["host_ip"], str):
                    query = query.filter_by(host_ip=filter_data["host_ip"])
                if isinstance(filter_data["host_ip"], list):
                    query = query.filter(models.Target.host_ip.in_(filter_data.get("host_ip")))
            if filter_data.get("scope", None):
                filter_data["scope"] = filter_data["scope"][0]
                query = query.filter_by(scope=self.config.ConvertStrToBool(filter_data.get("scope")))
            if filter_data.get("host_name", None):
                if isinstance(filter_data["host_name"], str):
                    query = query.filter_by(host_name=filter_data["host_name"])
                if isinstance(filter_data["host_name"], list):
                    query = query.filter(models.Target.host_name.in_(filter_data.get("host_name")))
            if filter_data.get("id", None):
                if isinstance(filter_data["id"], str):
                    query = query.filter_by(id=filter_data["id"])
                if isinstance(filter_data["id"], list):
                    query = query.filter(models.Target.id.in_(filter_data.get("id")))
        # This will allow new targets to be at the start
        query = query.order_by(models.Target.id.desc())
        if not for_stats:  # query for stats shouldn't have limit and offset
            try:
                if filter_data.get('offset', None):
                    if isinstance(filter_data.get('offset'), list):
                        filter_data['offset'] = filter_data['offset'][0]
                    query = query.offset(int(filter_data['offset']))
                if filter_data.get('limit', None):
                    if isinstance(filter_data.get('limit'), list):
                        filter_data['limit'] = filter_data['limit'][0]
                    if int(filter_data['limit']) != -1:
                        query = query.limit(int(filter_data['limit']))
            except ValueError:
                raise InvalidParameterType("Invalid parameter type for target db for id[lt] or id[gt]")
        return query

    @session_required
    def search_target_configs(self, filter_data=None, session_id=None):
        """Three things needed
        + Total number of targets
        + Filtered target dicts
        + Filtered number of targets

        :param filter_data: Filter data
        :type filter_data: `dict`
        :param session_id: session id
        :type session_id: `int`
        :return: results
        :rtype: `dict`
        """
        total = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id)).count()
        filtered_target_objs = self._generate_query(filter_data, session_id).all()
        filtered_number = self._generate_query(filter_data, session_id, for_stats=True).count()
        results = {
            "records_total": total,
            "records_filtered": filtered_number,
            "data": self.get_target_configs(filtered_target_objs)
        }
        return results

    @session_required
    def get_target_config_dicts(self, filter_data=None, session_id=None):
        """Get list of target config dicts

        :param filter_data: Filter criteria
        :type filter_data: `dict`
        :param session_id: session ID
        :type session_id: `int`
        :return: List of target config dicts
        :rtype: `list`
        """
        if filter_data is None:
            filter_data = {}
        target_obj_list = self._generate_query(filter_data, session_id).all()
        return self.get_target_configs(target_obj_list)

    def get_target_config_dict(self, target_obj):
        """Gets target config as a dict from object

        :param target_obj: target object
        :type target_obj:
        :return: Target config
        :rtype: `dict`
        """
        target_config = dict(TARGET_CONFIG)
        if target_obj:
            for key in list(TARGET_CONFIG.keys()):
                target_config[key] = getattr(target_obj, key)
            return target_config
        return None

    def get_target_configs(self, target_obj_list):
        """Get target list of configs

        :param target_obj_list: Target object list
        :type target_obj_list: `list`
        :return: List of target configs
        :rtype: `list`
        """
        target_configs = []
        for target_obj in target_obj_list:
            target_configs.append(self.get_target_config_dict(target_obj))
        return target_configs

    def get(self, key):
        """Get value of the key from target config

        :param key: Key
        :type key: `str`
        :return: Value
        :rtype: `str` #?
        """
        return self.target_config[key]

    def get_as_list(self, key_list):
        """Get everything as list

        :param key_list: Target key list
        :type key_list: `list`
        :return: Values list
        :rtype: `list`
        """
        values = []
        for key in key_list:
            values.append(self.get(key))
        return values

    def get_all(self, key):
        """Get all targets by key

        :param key: Target key
        :type key: `str`
        :return:
        :rtype:
        """
        results = self.db.session.query(getattr(models.Target, key.lower())).all()
        results = [result[0] for result in results]
        return results

    def get_all_in_scope(self, key):
        """Get all targets in scope by key

        :param key: Key
        :type key: `str`
        :return: List of target keys
        :rtype: `list`
        """
        results = self.db.session.query(getattr(models.Target, key.lower())).filter_by(scope=True).all()
        results = [result[0] for result in results]
        return results

    def is_url_in_scope(self, url):
        """To avoid following links to other domains.

        :param url: URL to check
        :type url: `str`
        :return: True if in scope
        :rtype: `bool`
        """
        parsed_url = urlparse(url)
        # Get all known Host Names in Scope.
        for host_name in self.get_all('host_name'):
            if parsed_url.hostname == host_name:
                return True
        return False

    def get_just_finished_targets(self):
        """Get recently finished targets

        :return: results
        :rtype: `dict`
        """
        results = []
        time15min = datetime.datetime.now() - datetime.timedelta(minutes=15)
        completed_targets = self.db.session.query(models.PluginOutput.target_id).filter(models.PluginOutput.end_time>=time15min).distinct(models.PluginOutput.target_id)
        running_targets = self.db.session.query(models.Work.target_id).distinct(models.Work.target_id)
        list_completed_targets = [target[0] for target in completed_targets]
        list_running_targets = [target[0] for target in running_targets]
        recently_finished_targets = [x for x in list_completed_targets if x not in list_running_targets]
        for target in recently_finished_targets:
            values = {}
            target_obj = self.db.session.query(models.Target).filter_by(id=target)
            values['target_id'] = target_obj[0].id
            values['target_url'] = target_obj[0].target_url
            results.append(values)
        return ({"data": results})

    @session_required
    def get_targets_by_severity_count(self, session_id=None):
        """Get targets by severity count

        :param session_id: session ID
        :type session_id: `int`
        :return: data
        :rtype: `dict`
        """
        filtered_severity_objs = []
        # "not ranked" = gray, "passing" = light green, "info" = light sky blue, "low" = blue, medium = yellow,
        # high = red, critical = dark purple
        severity_frequency = [
            {"id":0, "label": "Not Ranked", "value": 0, "color": "#A9A9A9"},
            {"id":1, "label": "Passing", "value": 0, "color": "#32CD32"},
            {"id":2, "label": "Info", "value": 0, "color": "#b1d9f4"},
            {"id":3, "label": "Low", "value": 0, "color": "#337ab7"},
            {"id":4, "label": "Medium", "value": 0, "color": "#ffcc00"},
            {"id":5, "label": "High", "value": 0, "color": "#c12e2a"},
            {"id":6, "label": "Critical", "value": 0, "color": "#800080"}
        ]
        total = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id)).count()
        target_objs = self.db.session.query(models.Target).filter(models.Target.sessions.any(id=session_id)).all()

        for target_obj in target_objs:
            if target_obj.max_user_rank != -1:
                severity_frequency[target_obj.max_user_rank + 1]["value"] += 100 / total
            else:
                severity_frequency[target_obj.max_owtf_rank + 1]["value"] += 100 / total

        for severity in severity_frequency:
            if severity["value"] != 0:
                filtered_severity_objs.append(severity)

        return {"data": filtered_severity_objs}
