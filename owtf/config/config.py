"""
owtf.config.config
~~~~~~~~~~~~~~~~~~

The Configuration object parses all configuration files, loads them into
memory, derives some settings and provides framework modules with a central
repository to get info.
"""

import os
import re
import logging
from copy import deepcopy

from owtf.utils.strings import multi_replace


try: #PY3
    from urllib.parse import urlparse
except ImportError:  #PY2
     from urlparse import urlparse
from collections import defaultdict

from owtf.error_handler import ErrorHandler
from owtf.utils.file import directory_access, get_output_dir, FileOperations
from owtf.utils.ip import get_ip_from_hostname, get_ips_from_hostname
from owtf.lib.exceptions import PluginAbortException, DBIntegrityException, UnresolvableTargetException
from owtf.lib.general import cprint
from owtf.managers import target as target_manager


REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = ['string', 'other']


class Config(object):

    root_dir = None
    owtf_pid = None
    config_path = os.path.expanduser(os.path.join("~", '.owtf', 'conf', 'framework.cfg'))
    profiles = {
        "GENERAL_PROFILE": None,
        "RESOURCES_PROFILE": None,
        "WEB_PLUGIN_ORDER_PROFILE": None,
        "NET_PLUGIN_ORDER_PROFILE": None,
        "MAPPING_PROFILE": None
    }
    target = None

    def __init__(self, root_dir, owtf_pid):
        """Initialize everything.

        :param root_dir: The root directory for owtf
        :type root_dir: `str`
        :param owtf_pid: The pid of the owtf parent process
        :type owtf_pid: `int`
        """
        self.root_dir = root_dir
        self.owtf_pid = owtf_pid
        self.error_handler = ErrorHandler()
        self.config = defaultdict(list)  # General configuration information.
        for type in CONFIG_TYPES:
            self.config[type] = {}        # key can consist alphabets, numbers, hyphen & underscore.
        self.search_regex = re.compile('%s([a-zA-Z0-9-_]*?)%s' % (REPLACEMENT_DELIMITER, REPLACEMENT_DELIMITER))
        # Available profiles = g -> General configuration, n -> Network plugin
        # order, w -> Web plugin order, r -> Resources file
        self.load_config_from_file(self.framework_config_file_path())

    def select_user_or_default_config_path(self, file_path, default_path=""):
        """If user config files are present return the passed file path, else the default config file path

        :param file_path: Path of config file to locate
        :param default_path: Default path of this file relative to "@@@root_dir@@@/configuration/" excluding filename
        :return: Absolute path of the file if found else default path
        """
        file_path = os.path.expanduser(file_path)
        if os.path.isfile(file_path):
            return file_path
        path = os.path.join(self.get_val("CONFIG_DIR"), default_path, os.path.basename(file_path))
        return path

    def framework_config_file_path(self):
        """Returns the full path to the configuration file in ~/.owtf or fallback to package specific file

        :return: path of the existing configuration file
        :rtype: `str`
        """
        if os.path.isfile(self.config_path):
            return self.config_path
        path = os.path.join(self.root_dir, 'data', 'conf', os.path.basename(self.config_path))
        return path

    def load_config_from_file(self, config_path):
        """Load the configuration into a global dictionary.

        :param config_path: The configuration file path
        :type config_path: `str`
        :return: None
        :rtype: None
        """
        cprint("Loading config from: %s.." % config_path)
        config_file = FileOperations.open(config_path, 'r')
        self.set_val('FRAMEWORK_DIR', self.root_dir)  # Needed Later.
        for line in config_file:
            try:
                key = line.split(':')[0]
                if key[0] == '#':  # Ignore comment lines.
                    continue
                value = line.replace("%s: " % key, "").strip()
                self.set_val(key,
                         multi_replace(value, {'FRAMEWORK_DIR': self.root_dir, 'OWTF_PID': str(self.owtf_pid)}))
            except ValueError:
                self.error_handler.abort_framework("Problem in config file: %s -> Cannot parse line: %s" % (
                    config_path, line))

    def process_phase1(self, options):
        """Process the options from the CLI.

        :param dict options: Options coming from the CLI.

        """
        # Backup the raw CLI options in case they are needed later.
        self.cli_options = deepcopy(options)

    def process_phase2(self, options):
        """Process the options for phase 2

        :param options: Options coming from the CLI.
        :type options: `dict`
        :return: None
        :rtype: None
        """
        target_urls = self.load_targets(options)
        self.load_works(target_urls, options)

    def load_works(self, target_urls, options):
        """Select the proper plugins to run against the target URLs.

        :param list target_urls: the target URLs
        :param dict options: the options from the CLI.

        """
        for target_url in target_urls:
            if target_url:
                self.load_work(target_url, options)

    def load_work(self, target_url, options):
        """Select the proper plugins to run against the target URL.

        .. note::

            If plugin group is not specified and several targets are fed, OWTF
            will run the WEB plugins for targets that are URLs and the NET
            plugins for the ones that are IP addresses.

        :param str target_url: the target URL
        :param dict options: the options from the CLI.
        """
        target = self.target.get_target_config_dicts({'target_url': target_url})
        group = options['PluginGroup']
        if options['OnlyPlugins'] is None:
            # If the plugin group option is the default one (not specified by the user).
            if group is None:
                group = 'web'  # Default to web plugins.
                # Run net plugins if target does not start with http (see #375).
                if not target_url.startswith(('http://', 'https://')):
                    group = 'network'
            filter_data = {'type': options['PluginType'], 'group': group}
        else:
            filter_data = {"code": options.get("OnlyPlugins"), "type": options.get("PluginType")}
        plugins = self.db_plugin.get_all(filter_data)
        if not plugins:
            logging.error("No plugin found matching type '%s' and group '%s' for target '%s'!" %
                          (options['PluginType'], group, target))
        self.worklist_manager.add_work(target, plugins, force_overwrite=options["Force_Overwrite"])

    def load_targets(self, options):
        """Load targets into the DB

        :param options: User supplied arguments
        :type options: `dict`
        :return: Added targets
        :rtype: `list`
        """
        scope = options['Scope']
        if options['PluginGroup'] == 'auxiliary':
            scope = self.get_aux_target(options)
        added_targets = []
        for target in scope:
            try:
                self.target.add_target(target)
                added_targets.append(target)
            except DBIntegrityException:
                logging.warning("%s already exists in DB" % target)
                added_targets.append(target)
            except UnresolvableTargetException as e:
                logging.error("%s" % e.parameter)
        return added_targets

    def get_aux_target(self, options):
        """This function returns the target for auxiliary plugins from the parameters provided

        :param options: User supplied arguments
        :type options: `dict`
        :return: List of targets for aux plugins
        :rtype: `list`
        """
        # targets can be given by different params depending on the aux plugin we are running
        # so "target_params" is a list of possible parameters by which user can give target
        target_params = ['RHOST', 'TARGET', 'SMB_HOST', 'BASE_URL', 'SMTP_HOST']
        plugin_params = self.get_component("plugin_params")
        targets = None
        if plugin_params.process_args():
            for param in target_params:
                if param in plugin_params.args:
                    targets = plugin_params.args[param]
                    break  # it will capture only the first one matched
            repeat_delim = ','
            if targets is None:
                logging.error("Aux target not found! See your plugin accepted parameters in ./plugins/ folder")
                return []
            if 'REPEAT_DELIM' in plugin_params.args:
                repeat_delim = plugin_params.args['REPEAT_DELIM']
            return targets.split(repeat_delim)
        else:
            return []

    def load_proxy_config(self, options):
        """Load proxy related configuration

        :param options: User supplied arguments
        :type options: `dict`
        :return: None
        :rtype: None
        """
        if options['InboundProxy']:
            if len(options['InboundProxy']) == 1:
                options['InboundProxy'] = [self.get_val('INBOUND_PROXY_IP'), options['InboundProxy'][0]]
        else:
            options['InboundProxy'] = [self.get_val('INBOUND_PROXY_IP'), self.get_val('INBOUND_PROXY_PORT')]
        self.set_val('INBOUND_PROXY_IP', options['InboundProxy'][0])
        self.set_val('INBOUND_PROXY_PORT', options['InboundProxy'][1])
        self.set_val('INBOUND_PROXY', ':'.join(options['InboundProxy']))
        self.set_val('PROXY', ':'.join(options['InboundProxy']))

    def get_resources(self, resource_type):
        """Replace the resources placeholders with the relevant config.

        :param resource_type: Type of resource to get
        :type resource_type: `str`
        :return: Fetched resource
        :rtype: `str`
        """
        return self.resource.get_resources(resource_type)

    def get_resource_list(self, resource_type_list):
        """Fetch the resource list

        :param resource_type_list: Type of resource list
        :type resource_type_list: `str`
        :return: Resource list
        :rtype: `list`
        """
        return self.resource.get_resource_list(resource_type_list)

    def get_raw_resources(self, resource_type):
        """Fetch the raw resource

        :param resource_type_list: Type of resource list
        :type resource_type_list: `str`
        :return: Resource
        :rtype: `str`
        """
        return self.resource[resource_type]

    def derive_config_from_url(self, target_URL):
        """Automatically find target information based on target name.

        .note::
            If target does not start with 'http' or 'https', then it is considered as a network target.

            + target host
            + target port
            + target url
            + target path
            + etc.

        :param target_URL: Target url supplied
        :type target_URL: `str`
        :return: Target config dictionary
        :rtype: `dict`
        """
        target_config = dict(target_manager.TARGET_CONFIG)
        target_config['target_url'] = target_URL
        try:
            parsed_url = urlparse(target_URL)
            if not parsed_url.hostname and not parsed_url.path:  # No hostname and no path, urlparse failed.
                raise ValueError
        except ValueError:  # Occurs sometimes when parsing invalid IPv6 host for instance
            raise UnresolvableTargetException("Invalid hostname '%s'" % str(target_URL))

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
                host, port = host.rsplit(':')
            except ValueError:  # Raised when target doesn't contain the port (e.g. google.fr)
                port = '80'
                if 'https' == url_scheme:
                    port = '443'
        else:  # Port found by urlparse.
            port = str(parsed_url.port)

        # Needed for google resource search.
        target_config['host_path'] = host_path
        # Some tools need this!
        target_config['url_scheme'] = url_scheme
        # Some tools need this!
        target_config['port_number'] = port
        # Set the top URL.
        target_config['host_name'] = host

        host_ip = get_ip_from_hostname(host)
        host_ips = get_ips_from_hostname(host)
        target_config['host_ip'] = host_ip
        target_config['alternative_ips'] = host_ips

        ip_url = target_config['target_url'].replace(host, host_ip)
        target_config['ip_url'] = ip_url
        target_config['top_domain'] = target_config['host_name']

        hostname_chunks = target_config['host_name'].split('.')
        if target_config['target_url'].startswith(('http', 'https')):  # target considered as hostname (web plugins)
            if not target_config['host_name'] in target_config['alternative_ips']:
                target_config['top_domain'] = '.'.join(hostname_chunks[1:])
            # Set the top URL (get "example.com" from "www.example.com").
            target_config['top_url'] = "%s://%s:%s" % (protocol, host, port)
        else:  # target considered as IP (net plugins)
            target_config['top_domain'] = ''
            target_config['top_url'] = ''
        return target_config

    def is_set(self, key):
        """Checks if the key is set in the config dict

        :param key: Key to check
        :type key: `str`
        :return: True if present, else False
        :rtype: `bool`
        """
        key = self.pad_key(key)
        config = self.get_config_dict()
        for type in CONFIG_TYPES:
            if key in config[type]:
                return True
        return False

    def get_key_val(self, key):
        """Gets the right config for target / general.

        :param key: The key
        :type key: `str`
        :return: Value for the key
        """
        config = self.get_config_dict()
        for type in CONFIG_TYPES:
            if key in config[type]:
                return config[type][key]

    def pad_key(self, key):
        """Add delimiters.

        :param key: Key to pad
        :type key: `str`
        :return: Padded key string
        :rtype: `str`
        """
        return REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER

    def strip_key(self, key):
        """Replaces key with empty space

        :param key: Key to clear
        :type key: `str`
        :return: Empty key
        :rtype: `str`
        """
        return key.replace(REPLACEMENT_DELIMITER, '')

    def get_val(self, key):
        """Transparently gets config info from target or General.

        :param key: Key
        :type key: `str`
        :return: The value for the key
        """
        try:
            key = self.pad_key(key)
            return self.get_key_val(key)
        except KeyError:
            message = "The configuration item: %s does not exist!" % key
            ErrorHandler.add(message)
            # Raise plugin-level exception to move on to next plugin.
            raise PluginAbortException(message)

    def get_logs_dir(self):
        """
        Get log directory by checking if abs or relative path is provided in
        config file
        """
        logs_dir = self.get_val("LOGS_DIR")
        # Check access for logs dir parent directory because logs dir may not be created.
        if os.path.isabs(logs_dir) and directory_access(os.path.dirname(logs_dir), "w+"):
            return logs_dir
        else:
            return os.path.join(get_output_dir(), logs_dir)

    def get_log_path(self, process_name):
        """Get the log file path based on the process name

        :param process_name: Process name
        :type process_name: `str`
        :return: Path to the specific log file
        :rtype: `str`
        """
        log_file_name = "%s.log" % process_name
        return os.path.join(self.get_logs_dir(), log_file_name)

    def get_as_list(self, key_list):
        """Get values for keys in a list

        :param key_list: List of keys
        :type key_list: `list`
        :return: List of corresponding values
        :rtype: `list`
        """
        value_list = []
        for key in key_list:
            value_list.append(self.get_val(key))
        return value_list

    def get_header_list(self, key):
        """Get list from a string of values for a key

        :param key: Key
        :type key: `str`
        :return: List of values
        :rtype: `list`
        """
        return self.get_val(key).split(',')

    def set_general_val(self, type, key, value):
        """ Set value for a key in any config file

        :param type: Type of config file, framework or general.cfg
        :type type: `str`
        :param key: The key
        :type key: `str`
        :param value: Value to be set
        :type value:
        :return: None
        :rtype: None
        """
        self.config[type][key] = value

    def set_val(self, key, value):
        """set config items in target-specific or General config."""
        # Store config in "replacement mode", that way we can multiple-replace
        # the config on resources, etc.
        key = REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER
        type = 'other'
        # Only when value is a string, store in replacements config.
        if isinstance(value, str):
            type = 'string'
        return self.set_general_val(type, key, value)

    def get_framework_config_dict(self):
        return self.get_config_dict()['string']

    def get_replacement_dict(self):
        """Returns a dictionary with framework directory path

        :return:
        :rtype:
        """
        return {"FRAMEWORK_DIR": self.root_dir}

    def __getitem__(self, key):
        return self.get_val(key)

    def __setitem__(self, key, value):
        return self.set_val(key, value)

    def get_config_dict(self):
        """Get the global config dictionary

        :return: None
        :rtype: None
        """
        return self.config

    def show(self):
        """Print all keys and values from configuration dictionary

        :return: None
        :rtype: None
        """
        logging.info("Configuration settings: ")
        for k, v in list(self.get_config_dict().items()):
            logging.info("%s => %s" % (str(k), str(v)))
