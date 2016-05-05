#!/usr/bin/env python
"""
The Configuration object parses all configuration files, loads them into
memory, derives some settings and provides framework modules with a central
repository to get info.
"""

import os
import re
import logging
import socket

from copy import deepcopy

from urlparse import urlparse
from collections import defaultdict

from framework.dependency_management.dependency_resolver import BaseComponent
from framework.dependency_management.interfaces import ConfigInterface

from framework.lib.exceptions import PluginAbortException, \
                                     DBIntegrityException, \
                                     UnresolvableTargetException
from framework.config import health_check
from framework.lib.general import cprint
from framework.db import models, target_manager
from framework.utils import is_internal_ip, directory_access, FileOperations


REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = ['string', 'other']


class Config(BaseComponent, ConfigInterface):

    COMPONENT_NAME = "config"

    RootDir = None
    OwtfPid = None
    Profiles = {
        "GENERAL_PROFILE": None,
        "RESOURCES_PROFILE": None,
        "WEB_PLUGIN_ORDER_PROFILE": None,
        "NET_PLUGIN_ORDER_PROFILE": None,
        "MAPPING_PROFILE": None
    }
    Target = None

    def __init__(self, root_dir, owtf_pid):
        self.register_in_service_locator()
        self.RootDir = root_dir
        self.OwtfPid = owtf_pid
        self.resource = None
        self.error_handler = None
        self.target = None
        self.Config = None
        self.db_plugin = None
        self.worklist_manager = None
        self.initialize_attributes()
        # key can consist alphabets, numbers, hyphen & underscore.
        self.SearchRegex = re.compile(
            REPLACEMENT_DELIMITER + '([a-zA-Z0-9-_]*?)' + REPLACEMENT_DELIMITER)
        # Available profiles = g -> General configuration, n -> Network plugin
        # order, w -> Web plugin order, r -> Resources file
        self.initialize_attributes()
        self.LoadFrameworkConfigFromFile(os.path.join(
            self.RootDir,
            'framework',
            'config',
            'framework_config.cfg'))

    def init(self):
        """Initialize the Option resources."""
        self.resource = self.get_component("resource")
        self.error_handler = self.get_component("error_handler")
        self.target = self.get_component("target")
        self.db_plugin = self.get_component("db_plugin")
        self.worklist_manager = self.get_component("worklist_manager")

    def initialize_attributes(self):
        self.Config = defaultdict(list)  # General configuration information.
        for type in CONFIG_TYPES:
            self.Config[type] = {}

    def LoadFrameworkConfigFromFile(self, config_path):
        """Load the configuration from into a global dictionary."""
        if 'framework_config' not in config_path:
            cprint("Loading Config from: " + config_path + " ..")
        config_file = FileOperations.open(config_path, 'r')
        self.Set('FRAMEWORK_DIR', self.RootDir)  # Needed Later.
        for line in config_file:
            try:
                key = line.split(':')[0]
                if key[0] == '#':  # Ignore comment lines.
                    continue
                value = line.replace(key + ": ", "").strip()
                self.Set(
                    key,
                    self.MultipleReplace(
                        value, {
                            'FRAMEWORK_DIR': self.RootDir,
                            'OWTF_PID': str(self.OwtfPid)}
                        )
                    )
            except ValueError:
                self.error_handler.FrameworkAbort(
                    "Problem in config file: '" + config_path +
                    "' -> Cannot parse line: " + line)

    def ConvertStrToBool(self, string):
        return (not(string in ['False', 'false', 0, '0']))

    def ProcessOptionsPhase1(self, options):
        """Process the options from the CLI.

        :param dict options: Options coming from the CLI.

        """
        # Backup the raw CLI options in case they are needed later.
        self.cli_options = deepcopy(options)
        self.LoadProfiles(options['Profiles'])

    def ProcessOptionsPhase2(self, options):
        target_urls = self.LoadTargets(options)
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
        target = self.target.GetTargetConfigs({'target_url': target_url})
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
            filter_data = {
                "code": options.get("OnlyPlugins"),
                "type": options.get("PluginType")}
        plugins = self.db_plugin.GetAll(filter_data)
        if not plugins:
            logging.error(
                "No plugin found matching type '%s' and group '%s' for target '%s'!" %
                (options['PluginType'], group, target))
        self.worklist_manager.add_work(
            target,
            plugins,
            force_overwrite=options["Force_Overwrite"])

    def get_profile_path(self, profile_name):
        return(self.Profiles.get(profile_name, None))

    def LoadProfiles(self, profiles):
        # This prevents python from blowing up when the Key does not exist :)
        self.Profiles = defaultdict(list)
        # Now override with User-provided profiles, if present.
        self.Profiles["GENERAL_PROFILE"] = profiles.get('g', None) or \
            self.FrameworkConfigGet("DEFAULT_GENERAL_PROFILE")
        # Resources profile
        self.Profiles["RESOURCES_PROFILE"] = profiles.get('r', None) or \
            self.FrameworkConfigGet("DEFAULT_RESOURCES_PROFILE")
        # web plugin order
        self.Profiles["WEB_PLUGIN_ORDER_PROFILE"] = profiles.get('w', None) or \
            self.FrameworkConfigGet("DEFAULT_WEB_PLUGIN_ORDER_PROFILE")
        # network plugin order
        self.Profiles["NET_PLUGIN_ORDER_PROFILE"] = profiles.get('n', None) or \
            self.FrameworkConfigGet("DEFAULT_NET_PLUGIN_ORDER_PROFILE")
        # mapping
        self.Profiles["MAPPING_PROFILE"] = profiles.get('m', None) or \
            self.FrameworkConfigGet("DEFAULT_MAPPING_PROFILE")

    def LoadTargets(self, options):
        scope = options['Scope']
        added_targets = []
        for target in scope:
            try:
                self.target.AddTarget(target)
                added_targets.append(target)
            except DBIntegrityException:
                logging.warning("%s already exists in DB" % target)
                added_targets.append(target)
            except UnresolvableTargetException as e:
                logging.error("%s" % e.parameter)
        return(added_targets)

    def MultipleReplace(self, text, replace_dict):
        new_text = text
        for key in self.SearchRegex.findall(new_text):
            # Check if key exists in the replace dict ;)
            if replace_dict.get(key, None):
                # A recursive call to remove all level occurences of place
                # holders.
                new_text = new_text.replace(
                    REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER,
                    self.MultipleReplace(replace_dict[key], replace_dict))
        return new_text

    def LoadProxyConfigurations(self, options):
        if options['InboundProxy']:
            if len(options['InboundProxy']) == 1:
                options['InboundProxy'] = [
                    self.Get('INBOUND_PROXY_IP'),
                    options['InboundProxy'][0]]
        else:
            options['InboundProxy'] = [
                self.Get('INBOUND_PROXY_IP'),
                self.Get('INBOUND_PROXY_PORT')]
        self.Set('INBOUND_PROXY_IP', options['InboundProxy'][0])
        self.Set('INBOUND_PROXY_PORT', options['InboundProxy'][1])
        self.Set('INBOUND_PROXY', ':'.join(options['InboundProxy']))
        self.Set('PROXY', ':'.join(options['InboundProxy']))

    def DeepCopy(self, config):
        """Perform a "deep" copy of the config Obj passed."""
        copy = defaultdict(list)
        for key, value in config.items():
            copy[key] = value.copy()
        return copy

    def GetResources(self, resource_type):
        """Replace the resources placeholders with the relevant config."""
        return self.resource.GetResources(resource_type)

    def GetResourceList(self, resource_type_list):
        return self.resource.GetResourceList(resource_type_list)

    def GetRawResources(self, resource_type):
        return self.Resources[resource_type]

    def DeriveConfigFromURL(self, target_URL):
        """Automatically find target information based on target name.

        If target does not start with 'http' or 'https', then it is considered as a network target.

        + target host
        + target port
        + target url
        + target path
        + etc.
        """
        target_config = dict(target_manager.TARGET_CONFIG)
        target_config['target_url'] = target_URL
        try:
            parsed_URL = urlparse(target_URL)
            if not parsed_URL.hostname and not parsed_URL.path:  # No hostname and no path, urlparse failed.
                raise ValueError
        except ValueError:  # Occurs sometimes when parsing invalid IPv6 host for instance
            raise UnresolvableTargetException("Invalid hostname '%s'" % str(target_URL))

        host = parsed_URL.hostname
        if not host:  # Happens when target is an IP (e.g. 127.0.0.1)
            host = parsed_URL.path  # Use the path as host (e.g. 127.0.0.1 => host = '' and path = '127.0.0.1')
            host_path = host
        else:
            host_path = parsed_URL.hostname + parsed_URL.path

        URL_scheme = parsed_URL.scheme
        protocol = parsed_URL.scheme
        if parsed_URL.port is None:  # Port is blank: Derive from scheme (default port set to 80).
            try:
                host, port = host.rsplit(':')
            except ValueError:  # Raised when target doesn't contain the port (e.g. google.fr)
                port = '80'
                if 'https' == URL_scheme:
                    port = '443'
        else:  # Port found by urlparse.
            port = str(parsed_URL.port)

        # Needed for google resource search.
        target_config['host_path'] = host_path
        # Some tools need this!
        target_config['url_scheme'] = URL_scheme
        # Some tools need this!
        target_config['port_number'] = port
        # Set the top URL.
        target_config['host_name'] = host

        host_IP = self.GetIPFromHostname(host)
        host_IPs = self.GetIPsFromHostname(host)
        target_config['host_ip'] = host_IP
        target_config['alternative_ips'] = host_IPs

        ip_url = target_config['target_url'].replace(host, host_IP)
        target_config['ip_url'] = ip_url
        target_config['top_domain'] = target_config['host_name']

        hostname_chunks = target_config['host_name'].split('.')
        if target_config['target_url'].startswith(('http', 'https')):  # Target considered as hostname (web plugins)
            if not target_config['host_name'] in target_config['alternative_ips']:
                target_config['top_domain'] = '.'.join(hostname_chunks[1:])
            # Set the top URL (get "example.com" from "www.example.com").
            target_config['top_url'] = protocol + "://" + host + ":" + port
        else:  # Target considered as IP (net plugins)
            target_config['top_domain'] = ''
            target_config['top_url'] = ''
        return target_config

    def DeriveOutputSettingsFromURL(self, target_URL):
        # Set the output directory.
        self.Set(
            'host_output',
            self.Get('OUTPUT_PATH') + "/" + self.Get('host_ip'))
        # Set the output directory.
        self.Set(
            'port_output',
            self.Get('host_output') + "/" + self.Get('port_number'))
        URL_info_ID = target_URL.replace('/','_').replace(':','')
        # Set the URL output directory (plugins will save their data here).
        self.Set(
            'url_output',
            self.Get('port_output') + "/" + URL_info_ID + "/")
        # Set the partial results path.
        self.Set('partial_url_output_path', self.Get('url_output')+'partial')
        self.Set(
            'PARTIAL_REPORT_REGISTER',
            self.Get('partial_url_output_path') + "/partial_report_register.txt")

        # Tested in FF 8: Different directory = Different localStorage!! -> All
        # localStorage-dependent reports must be on the same directory.
        # IMPORTANT: For localStorage to work Url reports must be on the same
        # directory.
        self.Set(
            'HTML_DETAILED_REPORT_PATH',
            self.Get('OUTPUT_PATH') + "/" + URL_info_ID + ".html")
        # IMPORTANT: For localStorage to work Url reports must be on the same
        # directory.
        self.Set(
            'URL_REPORT_LINK_PATH',
            self.Get('OUTPUT_PATH') + "/index.html")

        if not self.Get('SIMULATION'):
            FileOperations.create_missing_dirs(self.Get('host_output'))

        # URL Analysis DBs
        # URL DBs: Distintion between vetted, confirmed-to-exist, in
        # transaction DB URLs and potential URLs.
        self.InitHTTPDBs(self.Get('url_output'))

    def DeriveDBPathsFromURL(self, target_URL):
        targets_folder = os.path.expanduser(self.Get('TARGETS_DB_FOLDER'))
        url_info_id = target_URL.replace('/','_').replace(':','')
        transaction_db_path = os.path.join(
            targets_folder,
            url_info_id,
            "transactions.db")
        url_db_path = os.path.join(targets_folder, url_info_id, "urls.db")
        plugins_db_path = os.path.join(
            targets_folder,
            url_info_id,
            "plugins.db")
        return [transaction_db_path, url_db_path, plugins_db_path]

    def GetFileName(self, setting, partial=False):
        path = self.Get(setting)
        if partial:
            return os.path.basename(path)
        return path

    def GetHTMLTransaclog(self, partial=False):
        return self.GetFileName('TRANSACTION_LOG_HTML', partial)

    def GetTXTTransaclog(self, partial=False):
        return self.GetFileName('TRANSACTION_LOG_TXT', partial)

    def hostname_is_ip(self, hostname, ip):
        """Test if the hostname is an IP.

        :param str hostname: the hostname of the target.
        :param str ip: the IP (v4 or v6) of the target.

        :return: ``True`` if the hostname is an IP, ``False`` otherwise.
        :rtype: :class:`bool`

        """
        return hostname == ip

    def GetIPFromHostname(self, hostname):
        ip = ''
        # IP validation based on @marcwickenden's pull request, thanks!
        for sck in [socket.AF_INET, socket.AF_INET6]:
            try:
                socket.inet_pton(sck, hostname)
                ip = hostname
                break
            except socket.error:
                continue
        if not ip:
            try:
                ip = socket.gethostbyname(hostname)
            except socket.gaierror:
                raise UnresolvableTargetException(
                    "Unable to resolve: '%s'" % hostname)

        ipchunks = ip.strip().split("\n")
        alternative_IPs = []
        if len(ipchunks) > 1:
            ip = ipchunks[0]
            cprint(
                hostname + " has several IP addresses: (" +
                ", ".join(ipchunks)[0:-3] + "). Choosing first: " + ip + "")
            alternative_IPs = ipchunks[1:]
        self.Set('alternative_ips', alternative_IPs)
        ip = ip.strip()
        self.Set('INTERNAL_IP', is_internal_ip(ip))
        logging.info("The IP address for %s is: '%s'" % (hostname, ip))
        return ip

    def GetIPsFromHostname(self, hostname):
        ip = ''
        # IP validation based on @marcwickenden's pull request, thanks!
        for sck in [socket.AF_INET, socket.AF_INET6]:
            try:
                socket.inet_pton(sck, hostname)
                ip = hostname
                break
            except socket.error:
                continue
        if not ip:
            try:
                ip = socket.gethostbyname(hostname)
            except socket.gaierror:
                raise UnresolvableTargetException(
                    "Unable to resolve: '%s'" % hostname)

        ipchunks = ip.strip().split("\n")
        return ipchunks

    def IsSet(self, key):
        key = self.PadKey(key)
        config = self.GetConfig()
        for type in CONFIG_TYPES:
            if key in config[type]:
                return True
        return False

    def GetKeyValue(self, key):
        # Gets the right config for target / general.
        config = self.GetConfig()
        for type in CONFIG_TYPES:
            if key in config[type]:
                return config[type][key]

    def PadKey(self, key):
        # Add delimiters.
        return REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER

    def StripKey(self, key):
        return key.replace(REPLACEMENT_DELIMITER, '')

    def FrameworkConfigGet(self, key):
        """Transparently gets config info from Target or General."""
        try:
            key = self.PadKey(key)
            return self.GetKeyValue(key)
        except KeyError:
            message = "The configuration item: '" + key + "' does not exist!"
            self.error_handler.Add(message)
            # Raise plugin-level exception to move on to next plugin.
            raise PluginAbortException(message)

    def FrameworkConfigGetDBPath(self, key):
        # Only for main/common dbs, for target specific dbs, there are other
        # methods.
        relative_path = self.FrameworkConfigGet(key)
        return os.path.join(
            self.FrameworkConfigGet("OUTPUT_PATH"),
            self.FrameworkConfigGet("DB_DIR"),
            relative_path)

    def FrameworkConfigGetLogsDir(self):
        """
        Get log directory by checking if abs or relative path is provided in
        config file
        """
        logs_dir = self.FrameworkConfigGet("LOGS_DIR")
        # Check access for logsdir parent directory because logsdir may not be created.
        if os.path.isabs(logs_dir) and directory_access(os.path.dirname(logs_dir), "w+"):
            return logs_dir
        else:
            return os.path.join(self.GetOutputDir(), logs_dir)

    def FrameworkConfigGetLogPath(self, process_name):
        """
        Get the log file path based on the process name
        """
        log_file_name = process_name + ".log"
        return os.path.join(
            self.FrameworkConfigGetLogsDir(),
            log_file_name
        )

    def GetAsList(self, key_list):
        value_list = []
        for key in key_list:
            value_list.append(self.FrameworkConfigGet(key))
        return value_list

    def GetHeaderList(self, key):
        return self.FrameworkConfigGet(key).split(',')

    def SetGeneral(self, type, key, value):
        self.Config[type][key] = value

    def Set(self, key, value):
        """Set config items in Target-specific or General config."""
        # Store config in "replacement mode", that way we can multiple-replace
        # the config on resources, etc.
        key = REPLACEMENT_DELIMITER + key + REPLACEMENT_DELIMITER
        type = 'other'
        # Only when value is a string, store in replacements config.
        if isinstance(value, str):
            type = 'string'
        return self.SetGeneral(type, key, value)

    def GetFrameworkConfigDict(self):
        return self.GetConfig()['string']

    def GetReplacementDict(self):
        return({"FRAMEWORK_DIR":self.RootDir})

    def __getitem__(self, key):
        return self.Get(key)

    def __setitem__(self, key, value):
        return self.Set(key, value)

    def GetConfig(self):
        return self.Config

    def Show(self):
        cprint("Configuration settings")
        for k, v in self.GetConfig().items():
            cprint(str(k) + " => " + str(v))

    def GetOutputDir(self):
        output_dir = os.path.expanduser(self.FrameworkConfigGet("OUTPUT_PATH"))
        if not os.path.isabs(output_dir) and directory_access(os.getcwd(), "w+"):
            return output_dir
        else:
            # The output_dir may not be created yet, so check its parent.
            if directory_access(os.path.dirname(output_dir), "w+"):
                return output_dir
        return os.path.expanduser(os.path.join(self.FrameworkConfigGet("SETTINGS_DIR"), output_dir))

    def GetOutputDirForTargets(self):
        return os.path.join(
            self.GetOutputDir(),
            self.FrameworkConfigGet("TARGETS_DIR"))

    def CleanUpForTarget(self, target_URL):
        return FileOperations.rm_tree(self.GetOutputDirForTarget(target_URL))

    def GetOutputDirForTarget(self, target_URL):
        return os.path.join(
            self.GetOutputDirForTargets(),
            target_URL.replace("/", "_").replace(":", "").replace("#", ""))

    def CreateOutputDirForTarget(self, target_URL):
        FileOperations.create_missing_dirs(self.GetOutputDirForTarget(target_URL))

    def GetTransactionDBPathForTarget(self, target_URL):
        return os.path.join(
            self.GetOutputDirForTarget(target_URL),
            self.FrameworkConfigGet("TRANSACTION_DB_NAME"))

    def GetUrlDBPathForTarget(self, target_URL):
        return os.path.join(
            self.GetOutputDirForTarget(target_URL),
            self.FrameworkConfigGet("URL_DB_NAME"))

    def GetOutputDBPathForTarget(self, target_URL):
        return os.path.join(
            self.GetOutputDirForTarget(target_URL),
            self.FrameworkConfigGet("OUTPUT_DB_NAME"))
