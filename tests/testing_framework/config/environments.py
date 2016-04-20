from flexmock import flexmock
from framework.config.plugin import PluginConfig
from framework.config.config import Config
from framework.shell.blocking_shell import Shell
from os import path

PLUGINS_DIR = path.abspath("test_cases/resources/plugins_dir") + "/"   # Relative to the owtf/tests directory
WEB_TEST_GROUPS = path.abspath("../profile/plugin_web/groups.cfg")
NET_TEST_GROUPS = path.abspath("../profile/plugin_net/groups.cfg")
ROOT_DIR = path.abspath("..")


class PluginConfigEnvironmentBuilder():

    def __call__(self):
        self._prepare_core_mock()
        return PluginConfig(self.core_mock)

    def _prepare_core_mock(self):
        self.core_mock = flexmock()
        self.core_mock.Shell = Shell(self.core_mock)
        self.core_mock.Config = self._build_stub_for_config()
        self.core_mock.Error = self._build_stub_for_error_handler()

    def _build_stub_for_config(self):
        config = flexmock()
        config.should_receive("Get").with_args("PLUGINS_DIR").and_return(PLUGINS_DIR)
        config.should_receive("Get").with_args("WEB_TEST_GROUPS").and_return(WEB_TEST_GROUPS)
        config.should_receive("Get").with_args("NET_TEST_GROUPS").and_return(NET_TEST_GROUPS)
        return config

    def _build_stub_for_error_handler(self):
        error_handler = flexmock()
        error_handler.should_receive("FrameworkAbort")
        return error_handler


class ConfigEnvironmentBuilder():

    def __call__(self):
        self._create_core_mock()
        config = Config(RootDir=ROOT_DIR, CoreObj=self.core_mock)
        config.Plugin = self._get_plugin_config_instance()
        return config

    def _create_core_mock(self):
        self.core_mock = flexmock()
        self.core_mock.CreateMissingDirs = lambda dirs: dirs  # Some error with flexmock when stubbing CreateMissingDirs
        self.core_mock.should_receive("GetPartialPath")
        self.core_mock.IsIPInternal = lambda ip: True
        self.core_mock.Error = self._create_error_handler_mock()
        self.core_mock.ProxyMode = None

    def _create_error_handler_mock(self):
        error_handler = flexmock()
        error_handler.should_receive("FrameworkAbort")
        error_handler.should_receive("Add")
        return error_handler

    def _get_plugin_config_instance(self):
        plugin_config_builder = PluginConfigEnvironmentBuilder()
        plugin_config = plugin_config_builder()
        return plugin_config

