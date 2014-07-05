#!/usr/bin/env python
"""

owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The Configuration object parses all configuration files, loads them into
memory, derives some settings and provides framework modules with a central
repository to get info.

"""

import os
import re
import socket

from urlparse import urlparse
from collections import defaultdict

from framework.lib.exceptions import PluginAbortException, \
                                     DBIntegrityException, \
                                     UnresolvableTargetException
from framework.config import health_check
from framework.lib.general import cprint
from framework.db import models, target_manager


REPLACEMENT_DELIMITER = "@@@"
REPLACEMENT_DELIMITER_LENGTH = len(REPLACEMENT_DELIMITER)
CONFIG_TYPES = [ 'string', 'other' ]


class Config(object):
    Target = None
    def __init__(self, root_dir, owtf_pid, core):
        self.RootDir = root_dir
        self.OwtfPid = owtf_pid
        self.Core = core
        self.initialize_attributes()
        # key can consist alphabets, numbers, hyphen & underscore.
        self.SearchRegex = re.compile(
            REPLACEMENT_DELIMITER + '([A-Z0-9-_]*?)' + REPLACEMENT_DELIMITER)
        # Available profiles = g -> General configuration, n -> Network plugin
        # order, w -> Web plugin order, r -> Resources file
        self.LoadFrameworkConfigFromFile(
            self.RootDir + '/framework/config/framework_config.cfg')

    def initialize_attributes(self):
        self.Config = defaultdict(list)  # General configuration information.
        for type in CONFIG_TYPES:
            self.Config[type] = {}

    def Init(self):
        self.HealthCheck = health_check.HealthCheck(self.Core)

    def LoadFrameworkConfigFromFile(self, config_path):
        """Load the configuration from into a global dictionary."""
        if 'framework_config' not in config_path:
            cprint("Loading Config from: " + config_path + " ..")
        config_file = self.Core.open(config_path, 'r')
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
                self.Core.Error.FrameworkAbort(
                    "Problem in config file: '" + config_path +
                    "' -> Cannot parse line: " + line)

    def ConvertStrToBool(self, string):
        return (not(string in ['False', 'false', 0, '0']))

    def ProcessOptions(self, options):
        self.LoadProfiles(options['Profiles'])
        self.LoadTargets(options)

    def LoadProfiles(self, profiles):
        # This prevents python from blowing up when the Key does not exist :)
        self.Profiles = defaultdict(list)
        # Now override with User-provided profiles, if present.
        for type, file in profiles:
            self.Profiles[type] = file

    def LoadTargets(self, options):
        scope = self.PrepareURLScope(options['Scope'], options['PluginGroup'])
        for target in scope:
            try:
                self.Core.DB.Target.AddTarget(target)
            except DBIntegrityException:
                cprint(target + " already exists in DB")
            except UnresolvableTargetException as e:
                cprint(e.parameter)

    def PrepareURLScope(self, scope, group):
        """Convert all targets to URLs."""
        new_scope = []
        for target_URL in scope:
            if target_URL[-1] == "/":
                target_URL = target_URL[0:-1]
            if target_URL[0:4] != 'http':
                # Add both "http" and "https" if not present:
                # The connection check will then remove from the report if one
                # does not exist.
                if group == "net":
                    new_scope.append('http://' + target_URL)
                else:
                    for prefix in ['http', 'https']:
                        new_scope.append(prefix + '://' + target_URL)
            else:
                new_scope.append(target_URL)  # Append "as-is".
        return new_scope

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
        return self.Core.DB.Resource.GetResources(resource_type)

    def GetResourceList(self, resource_type_list):
        return self.Core.DB.Resource.GetResourceList(resource_type_list)

    def GetRawResources(self, resource_type):
        return self.Resources[resource_type]

    def DeriveConfigFromURL(self, target_URL):
        target_config = dict(target_manager.TARGET_CONFIG)
        # Set the target in the config.
        target_config['TARGET_URL'] = target_URL
        # TODO: Use urlparse here.
        parsed_URL = urlparse(target_URL)
        URL_scheme = parsed_URL.scheme
        protocol = parsed_URL.scheme
        if parsed_URL.port == None:  # Port is blank: Derive from scheme.
            port = '80'
            if 'https' == URL_scheme:
                port = '443'
        else:  # Port found by urlparse.
            port = str(parsed_URL.port)
        host = parsed_URL.hostname
        host_path = parsed_URL.hostname + parsed_URL.path
        # Needed for google resource search.
        target_config['HOST_PATH'] = host_path
        # Some tools need this!
        target_config['URL_SCHEME'] = URL_scheme
        # Some tools need this!
        target_config['PORT_NUMBER'] = port
        # Set the top URL.
        target_config['HOST_NAME'] = host

        host_IP = self.GetIPFromHostname(host)
        host_IPs = self.GetIPsFromHostname(host)
        target_config['HOST_IP'] = host_IP
        target_config['ALTERNATIVE_IPS'] = host_IPs

        IP_URL = target_config['TARGET_URL'].replace(host, host_IP)
        target_config['IP_URL'] = IP_URL
        target_config['TOP_DOMAIN'] = target_config['HOST_NAME']

        hostname_chunks = target_config['HOST_NAME'].split('.')
        if self.IsHostNameNOTIP(host, host_IP) and len(hostname_chunks) > 2:
            # Get "example.com" from "www.example.com"
            target_config['TOP_DOMAIN'] = '.'.join(hostname_chunks[1:])
        # Set the top URL.
        target_config['TOP_URL'] = protocol + "://" + host + ":" + port
        return target_config

    def DeriveOutputSettingsFromURL(self, target_URL):
        # Set the output directory.
        self.Set(
            'HOST_OUTPUT',
            self.Get('OUTPUT_PATH') + "/" + self.Get('HOST_IP'))
        # Set the output directory.
        self.Set(
            'PORT_OUTPUT',
            self.Get('HOST_OUTPUT') + "/" + self.Get('PORT_NUMBER'))
        URL_info_ID = target_URL.replace('/','_').replace(':','')
        # Set the URL output directory (plugins will save their data here).
        self.Set(
            'URL_OUTPUT',
            self.Get('PORT_OUTPUT') + "/" + URL_info_ID + "/")
        # Set the partial results path.
        self.Set('PARTIAL_URL_OUTPUT_PATH', self.Get('URL_OUTPUT')+'partial')
        self.Set(
            'PARTIAL_REPORT_REGISTER',
            self.Get('PARTIAL_URL_OUTPUT_PATH') + "/partial_report_register.txt")

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
            self.Core.CreateMissingDirs(self.Get('HOST_OUTPUT'))

        # URL Analysis DBs
        # URL DBs: Distintion between vetted, confirmed-to-exist, in
        # transaction DB URLs and potential URLs.
        self.InitHTTPDBs(self.Get('URL_OUTPUT'))

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

    def IsHostNameNOTIP(self, host_name, host_ip):
        return host_name != host_ip  # Host.

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
                    "Unable to resolve : " + hostname);

        ipchunks = ip.strip().split("\n")
        alternative_IPs = []
        if len(ipchunks) > 1:
            ip = ipchunks[0]
            cprint(
                hostname + " has several IP addresses: (" +
                ", ".join(ipchunks)[0:-3] + "). Choosing first: " + ip + "")
            alternative_IPs = ipchunks[1:]
        self.Set('ALTERNATIVE_IPS', alternative_IPs)
        ip = ip.strip()
        self.Set('INTERNAL_IP', self.Core.IsIPInternal(ip))
        cprint("The IP address for " + hostname + " is: '" + ip + "'")
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
                    "Unable to resolve : " + hostname);

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
            self.Core.Error.Add(message)
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

    def GetAsPartialPath(self, key):
        """Convenience wrapper."""
        return self.Core.GetPartialPath(self.Get(key))

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

    def GetOutputDirForTargets(self):
        return os.path.join(
            self.FrameworkConfigGet("OUTPUT_PATH"),
            self.FrameworkConfigGet("TARGETS_DIR"))

    def CleanUpForTarget(self, target_URL):
        return self.Core.rmtree(self.GetOutputDirForTarget(target_URL))

    def GetOutputDirForTarget(self, target_URL):
        return os.path.join(
            self.GetOutputDirForTargets(),
            target_URL.replace("/", "_").replace(":", ""))

    def CreateOutputDirForTarget(self, target_URL):
        self.Core.CreateMissingDirs(self.GetOutputDirForTarget(target_URL))

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
