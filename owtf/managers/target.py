"""
owtf.managers.target
~~~~~~~~~~~~~~~~~~~~

"""
import logging
import os

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from owtf.db.session import get_count, get_scoped_session
from owtf.lib.exceptions import (
    DBIntegrityException,
    InvalidParameterType,
    InvalidTargetReference,
    UnresolvableTargetException,
)
from owtf.models.command import Command
from owtf.models.session import Session
from owtf.models.target import Target
from owtf.managers.session import add_target_to_session, session_required
from owtf.plugin.params import plugin_params
from owtf.settings import OUTPUT_PATH
from owtf.utils.file import (
    cleanup_target_dirs,
    create_output_dir_target,
    get_target_dir,
)
from owtf.utils.ip import get_ip_from_hostname, get_ips_from_hostname
from owtf.utils.strings import str2bool, to_str


TARGET_CONFIG = {
    "id": 0,
    "target_url": "",
    "host_name": "",
    "host_path": "",
    "url_scheme": "",
    "port_number": "",  # In str form
    "host_ip": "",
    "alternative_ips": "",  # str(list), so it can easily reversed using list(str)
    "ip_url": "",
    "top_domain": "",
    "top_url": "",
    "scope": True,
    "max_user_rank": -1,
    "max_owtf_rank": -1,
}

PATH_CONFIG = {
    "partial_url_output_path": "",
    "host_output": "",
    "port_output": "",
    "url_output": "",
    "plugin_output_dir": "",
}


def target_required(func):
    """
    In order to use this decorator on a `method` there are two requirements
    + target_id must be a kwarg of the function
    + Core must be attached to the object at Core

    All this decorator does is check if a valid value is passed for target_id
    if not get the target_id from target manager and pass it
    """

    def wrapped_function(*args, **kwargs):
        if "target_id" not in kwargs:
            kwargs["target_id"] = target_manager.get_target_id
        return func(*args, **kwargs)

    return wrapped_function


@target_required
def command_already_registered(session, original_command, target_id=None):
    """Checks if the command has already been registered
    :param original_command: Original command to check
    :type original_command: `dict`
    :param target_id: Target ID
    :type target_id: `int`
    :return: None
    :rtype: None
    """
    from owtf.managers.poutput import plugin_output_exists

    if target_id is not None:
        target_manager.set_target(target_id)

    register_entry = session.query(Command).get(original_command)
    if register_entry:
        # If the command was completed and the plugin output to which it
        # is referring exists
        if register_entry.success:
            if plugin_output_exists(
                session, register_entry.plugin_key, register_entry.target_id
            ):
                return get_target_url_for_id(session, register_entry.target_id)
            else:
                Command.delete_cmd(session, original_command)
                return None
        else:  # Command failed
            Command.delete_cmd(session, original_command)
            return get_target_url_for_id(session, register_entry.target_id)
    return None


class TargetManager(object):
    # All these variables reflect to current target which is referenced by a unique ID
    target_id = None
    target_config = dict(TARGET_CONFIG)
    path_config = dict(PATH_CONFIG)

    def __init__(self):
        self.session = get_scoped_session()

    def set_target(self, target_id):
        """Set a target by ID
        :param target_id: target ID
        :type target_id: `int`
        :return: None
        :rtype: None
        """
        try:
            self.target_id = target_id
            self.target_config = get_target_config_by_id(self.session, target_id)
            self.path_config = self.get_path_configs(self.target_config)
        except InvalidTargetReference:
            raise InvalidTargetReference(
                "0. Target doesn't exist: {!s}".format(target_id)
            )

    def get_path_configs(self, target_config):
        """Get paths to output directories

        :param target_config: Target config
        :type target_config: `dict`
        :return: Path config
        :rtype: `dict`
        """
        path_config = {}
        # Set the output directory.
        path_config["host_output"] = os.path.join(OUTPUT_PATH, target_config["host_ip"])
        path_config["port_output"] = os.path.join(
            path_config["host_output"], target_config["port_number"]
        )
        # Set the URL output directory (plugins will save their data here).
        path_config["url_output"] = os.path.join(
            get_target_dir(target_config["target_url"])
        )
        # Set the partial results path.
        path_config["partial_url_output_path"] = os.path.join(
            path_config["url_output"], "partial"
        )
        return path_config

    @property
    def get_target_id(self):
        """Return target ID
        :return: target ID
        :rtype: `int`
        """
        return self.target_id

    def get_val(self, key):
        """Get value of the key from target config
        :param key: Key
        :type key: `str`
        :return: Value
        :rtype: `str` #?
        """
        return self.target_config[key]

    def get_target_url(self):
        """Return target URL
        :return: Target URL
        :rtype: `str`
        """
        return self.get_val("target_url")

    def get_target_urls(self):
        """Return target URLs
        :return: List of target urls
        :rtype: `list`
        """
        return get_all_targets(self.session, "target_url")

    @property
    def get_target_config(self):
        """Return target config
        :return: Target config
        :rtype: `dict`
        """
        return self.target_config

    @property
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
def add_target(session, target_url, session_id=None):
    """Adds a target to session

    :param target_url: Target url
    :type target_url: `str`
    :param session_id: session ID
    :type session_id: `int`
    :return: None
    :rtype: None
    """
    if target_url not in get_all_targets(session, "target_url"):
        # A try-except can be used here, but then ip-resolution takes time
        # even if target is present
        target_config = derive_config_from_url(target_url)
        config_obj = Target(target_url=target_url)
        config_obj.host_name = target_config["host_name"]
        config_obj.host_path = target_config["host_path"]
        config_obj.url_scheme = target_config["url_scheme"]
        config_obj.port_number = target_config["port_number"]
        config_obj.host_ip = target_config["host_ip"]
        config_obj.alternative_ips = str(target_config["alternative_ips"])
        config_obj.ip_url = target_config["ip_url"]
        config_obj.top_domain = target_config["top_domain"]
        config_obj.top_url = target_config["top_url"]
        session.add(config_obj)
        config_obj.sessions.append(session.query(Session).get(session_id))
        session.commit()
        target_id = config_obj.id
        create_missing_dirs_target(target_url)
        target_manager.set_target(target_id)
    else:
        session_obj = session.query(Session).get(session_id)
        target_obj = session.query(Target).filter_by(target_url=target_url).one()
        if session_obj in target_obj.sessions:
            raise DBIntegrityException(
                "{!s} already present in Target DB & session".format(target_url)
            )
        else:
            add_target_to_session(session, target_obj.id, session_id=session_obj.id)


@session_required
def add_targets(session, target_urls, session_id=None):
    """Add multiple targets

    :param target_urls: List of target urls
    :type target_urls: `list`
    :param session_id: session ID
    :type session_id: `int`
    :return: None
    :rtype: None
    """
    for target_url in target_urls:
        add_target(session, to_str(target_url), session_id=session_id)


def update_target(session, data_dict, target_url=None, id=None):
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
        target_obj = session.query(Target).get(id)
    if target_url:
        target_obj = session.query(Target).filter_by(target_url=target_url).one()
    if not target_obj:
        raise InvalidTargetReference(
            "2. Target doesn't exist: {!s}".format(id) if id else str(target_url)
        )
    # TODO: Updating all related attributes when one attribute is changed
    if data_dict.get("scope", None) is not None:
        target_obj.scope = str2bool(data_dict.get("scope", None))
    session.commit()


def delete_target(session, target_url=None, id=None):
    """Delete a target from DB

    :param target_url: target URL
    :type target_url: `str`
    :param id: Target ID
    :type id: `int`
    :return: None
    :rtype: None
    """
    target_obj = None
    if id:
        target_obj = session.query(Target).get(id)
    if target_url:
        target_obj = session.query(Target).filter_by(target_url=target_url).one()
    if not target_obj:
        raise InvalidTargetReference(
            "3. Target doesn't exist: {!s}".format(id) if id else str(target_url)
        )
    if target_obj:
        target_url = target_obj.target_url
        session.delete(target_obj)
        session.commit()
    cleanup_target_dirs(target_url)


def create_missing_dirs_target(target_url):
    """Creates missing output dirs for target

    :param target_url: Target URL
    :type target_url: `str`
    :return: None
    :rtype: None
    """
    create_output_dir_target(target_url)


def get_target_url_for_id(session, id):
    """Get target URL by target ID

    :param id: target ID
    :type id: `int`
    :return: Target url
    :rtype: `str`
    """
    target_obj = session.query(Target).get(id)
    if not target_obj:
        logging.info("Failing with ID: %s" % str(id))
        raise InvalidTargetReference("1. Target doesn't exist with ID: {!s}".format(id))
    return target_obj.target_url


def get_target_config_by_id(session, id):
    """Get target config by id

    :param id: Target id
    :type id: `int`
    :return: Config dict
    :rtype: `dict`
    """
    target_obj = session.query(Target).get(id)
    if not target_obj:
        raise InvalidTargetReference("5. Target doesn't exist: {!s}".format(id))
    return get_target_config_dict(target_obj)


def target_gen_query(session, filter_data, session_id, for_stats=False):
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
    query = session.query(Target).filter(Target.sessions.any(id=session_id))
    if filter_data.get("search") is not None:
        if filter_data.get("target_url", None):
            if isinstance(filter_data.get("target_url"), list):
                filter_data["target_url"] = filter_data["target_url"][0]
            query = query.filter(
                Target.target_url.like("%%{!s}%%".format(filter_data["target_url"]))
            )
    else:
        if filter_data.get("target_url", None):
            if isinstance(filter_data["target_url"], str):
                query = query.filter_by(target_url=filter_data["target_url"])
            if isinstance(filter_data["target_url"], list):
                query = query.filter(
                    Target.target_url.in_(filter_data.get("target_url"))
                )
        if filter_data.get("host_ip", None):
            if isinstance(filter_data["host_ip"], str):
                query = query.filter_by(host_ip=filter_data["host_ip"])
            if isinstance(filter_data["host_ip"], list):
                query = query.filter(Target.host_ip.in_(filter_data.get("host_ip")))
        if filter_data.get("scope", None):
            filter_data["scope"] = filter_data["scope"][0]
            query = query.filter_by(scope=str2bool(filter_data.get("scope")))
        if filter_data.get("host_name", None):
            if isinstance(filter_data["host_name"], str):
                query = query.filter_by(host_name=filter_data["host_name"])
            if isinstance(filter_data["host_name"], list):
                query = query.filter(Target.host_name.in_(filter_data.get("host_name")))
        if filter_data.get("id", None):
            if isinstance(filter_data["id"], str):
                query = query.filter_by(id=filter_data["id"])
            if isinstance(filter_data["id"], list):
                query = query.filter(Target.id.in_(filter_data.get("id")))
    # This will allow new targets to be at the start
    query = query.order_by(Target.id.desc())
    if not for_stats:  # query for stats shouldn't have limit and offset
        try:
            if filter_data.get("offset", None):
                if isinstance(filter_data.get("offset"), list):
                    filter_data["offset"] = filter_data["offset"][0]
                query = query.offset(int(filter_data["offset"]))
            if filter_data.get("limit", None):
                if isinstance(filter_data.get("limit"), list):
                    filter_data["limit"] = filter_data["limit"][0]
                if int(filter_data["limit"]) != -1:
                    query = query.limit(int(filter_data["limit"]))
        except ValueError:
            raise InvalidParameterType(
                "Invalid parameter type for target db for id[lt] or id[gt]"
            )
    return query


@session_required
def search_target_configs(session, filter_data=None, session_id=None):
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
    total = get_count(session.query(Target).filter(Target.sessions.any(id=session_id)))
    filtered_target_objs = target_gen_query(session, filter_data, session_id).all()
    filtered_number = get_count(
        target_gen_query(session, filter_data, session_id, for_stats=True)
    )
    results = {
        "records_total": total,
        "records_filtered": filtered_number,
        "data": get_target_configs(filtered_target_objs),
    }
    return results


@session_required
def get_target_config_dicts(session, filter_data=None, session_id=None):
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
    target_obj_list = target_gen_query(
        session=session, filter_data=filter_data, session_id=session_id
    ).all()
    return get_target_configs(target_obj_list)


def get_target_config_dict(target_obj):
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


def get_target_configs(target_obj_list):
    """Get target list of configs

    :param target_obj_list: Target object list
    :type target_obj_list: `list`
    :return: List of target configs
    :rtype: `list`
    """
    target_configs = []
    for target_obj in target_obj_list:
        target_configs.append(get_target_config_dict(target_obj))
    return target_configs


def get_targets_as_list(key_list):
    """Get everything as list

    :param key_list: Target key list
    :type key_list: `list`
    :return: Values list
    :rtype: `list`
    """
    session = get_scoped_session()
    values = []
    for key in key_list:
        values.append(get_all_targets(session, key))
    return values


def get_all_targets(session, key):
    """Get all targets by key

    :param key: Target key
    :type key: `str`
    :return:
    :rtype:
    """
    results = session.query(getattr(Target, key.lower())).all()
    results = [result[0] for result in results]
    return results


def get_all_in_scope(key):
    """Get all targets in scope by key

    :param key: Key
    :type key: `str`
    :return: List of target keys
    :rtype: `list`
    """
    session = get_scoped_session()
    results = session.query(getattr(Target, key.lower())).filter_by(scope=True).all()
    results = [result[0] for result in results]
    return results


def is_url_in_scope(url):
    """To avoid following links to other domains.

    :param url: URL to check
    :type url: `str`
    :return: True if in scope
    :rtype: `bool`
    """
    parsed_url = urlparse(url)
    # Get all known Host Names in Scope.
    for host_name in get_all_in_scope(key="host_name"):
        if parsed_url.hostname == host_name:
            return True
    return False


def load_targets(session, options):
    """Load targets into the DB

    :param options: User supplied arguments
    :type options: `dict`
    :return: Added targets
    :rtype: `list`
    """
    scope = options["scope"]
    if options["plugin_group"] == "auxiliary":
        scope = get_aux_target()
    added_targets = []
    for target in scope:
        try:
            add_target(session=session, target_url=target)
            added_targets.append(target)
        except DBIntegrityException:
            logging.warning("%s already exists in DB", target)
            added_targets.append(target)
        except UnresolvableTargetException as e:
            logging.error("%s", e.parameter)
    return added_targets


def get_aux_target():
    """This function returns the target for auxiliary plugins from the parameters provided

    :param options: User supplied arguments
    :type options: `dict`
    :return: List of targets for aux plugins
    :rtype: `list`
    """
    # targets can be given by different params depending on the aux plugin we are running
    # so "target_params" is a list of possible parameters by which user can give target
    target_params = ["RHOST", "TARGET", "SMB_HOST", "BASE_URL", "SMTP_HOST"]
    targets = None
    if plugin_params.process_args():
        for param in target_params:
            if param in plugin_params.args:
                targets = plugin_params.args[param]
                break  # it will capture only the first one matched
        repeat_delim = ","
        if targets is None:
            logging.error(
                "Aux target not found! See your plugin accepted parameters in ./plugins/ folder"
            )
            return []
        if "REPEAT_DELIM" in plugin_params.args:
            repeat_delim = plugin_params.args["REPEAT_DELIM"]
        return targets.split(repeat_delim)
    else:
        return []


@session_required
def get_targets_by_severity_count(session, session_id=None):
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
        {"id": 0, "label": "Not Ranked", "value": 0, "color": "#A9A9A9"},
        {"id": 1, "label": "Passing", "value": 0, "color": "#32CD32"},
        {"id": 2, "label": "Info", "value": 0, "color": "#b1d9f4"},
        {"id": 3, "label": "Low", "value": 0, "color": "#337ab7"},
        {"id": 4, "label": "Medium", "value": 0, "color": "#ffcc00"},
        {"id": 5, "label": "High", "value": 0, "color": "#c12e2a"},
        {"id": 6, "label": "Critical", "value": 0, "color": "#800080"},
    ]
    total = session.query(Target).filter(Target.sessions.any(id=session_id)).count()
    target_objs = session.query(Target).filter(Target.sessions.any(id=session_id)).all()

    for target_obj in target_objs:
        if target_obj.max_user_rank != -1:
            severity_frequency[target_obj.max_user_rank + 1]["value"] += 100 / total
        else:
            severity_frequency[target_obj.max_owtf_rank + 1]["value"] += 100 / total

    for severity in severity_frequency:
        if severity["value"] != 0:
            filtered_severity_objs.append(severity)

    return {"data": filtered_severity_objs}


def derive_config_from_url(target_url):
    """Automatically find target information based on target name.

    .. note::
        If target does not start with 'http' or 'https', then it is considered as a network target.

    :param target_URL: Target url supplied
    :type target_URL: `str`
    :return: Target config dictionary
    :rtype: `dict`
    """
    target_config = dict(TARGET_CONFIG)
    target_config["target_url"] = target_url
    try:
        parsed_url = urlparse(target_url)
        if (
            not parsed_url.hostname and not parsed_url.path
        ):  # No hostname and no path, urlparse failed.
            raise ValueError
    except ValueError:  # Occurs sometimes when parsing invalid IPv6 host for instance
        raise UnresolvableTargetException("Invalid hostname '{!s}'".format(target_url))

    host = parsed_url.hostname
    if not host:  # Happens when target is an IP (e.g. 127.0.0.1)
        host = parsed_url.path  # Use the path as host (e.g. 127.0.0.1 => host = '' and path = '127.0.0.1')
        host_path = host
    else:
        host_path = parsed_url.hostname + parsed_url.path

    url_scheme = parsed_url.scheme
    protocol = parsed_url.scheme
    if parsed_url.port is None:  # Port is blank: Derive from scheme (default port set to 80).
        try:
            host, port = host.rsplit(":")
        except ValueError:  # Raised when target doesn't contain the port (e.g. google.fr)
            port = "80"
            if "https" == url_scheme:
                port = "443"
    else:  # Port found by urlparse.
        port = str(parsed_url.port)

    # Needed for google resource search.
    target_config["host_path"] = host_path
    # Some tools need this!
    target_config["url_scheme"] = url_scheme
    # Some tools need this!
    target_config["port_number"] = port
    # Set the top URL.
    target_config["host_name"] = host

    host_ip = get_ip_from_hostname(host)
    host_ips = get_ips_from_hostname(host)
    target_config["host_ip"] = host_ip
    target_config["alternative_ips"] = host_ips

    ip_url = target_config["target_url"].replace(host, host_ip)
    target_config["ip_url"] = ip_url
    target_config["top_domain"] = target_config["host_name"]

    hostname_chunks = target_config["host_name"].split(".")
    if target_config["target_url"].startswith(
        ("http", "https")
    ):  # target considered as hostname (web plugins)
        if not target_config["host_name"] in target_config["alternative_ips"]:
            target_config["top_domain"] = ".".join(hostname_chunks[1:])
        # Set the top URL (get "example.com" from "www.example.com").
        target_config["top_url"] = "{0}://{1}:{2}".format(protocol, host, port)
    else:  # target considered as IP (net plugins)
        target_config["top_domain"] = ""
        target_config["top_url"] = ""
    return target_config


# Define the service
target_manager = TargetManager()
