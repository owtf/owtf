from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from hamcrest import *
from framework.plugin.plugin_handler import PluginHandler
from tests.testing_framework.utils import ExpensiveResourceProxy
from tests.testing_framework.config.environments import PluginConfigEnvironmentBuilder
from tests.testing_framework.plugin.environments import PluginHandlerEnvironmentBuilder
from os import path
from framework.lib.exceptions import PluginAbortException,\
                                     UnreachableTargetException
from tests.testing_framework.doubles.mock import OrderedExecutionMock
import multiprocessing
import time
import sys
from os import path
import Queue
import unittest

PLUGINS_DIR = path.abspath("test_cases/resources_plugins_dir") + "/"


class PluginHandlerTests(BaseTestCase):

    def before(self):
        self.plugin_handler = PluginHandlerEnvironmentBuilder().get_plugin_handler()
        self.core_mock = self.plugin_handler.Core

    def test_LogPluginExecution_logs_a_plugin_in_the_internal_dictionary(self):
        self.core_mock.Config.should_receive("GetTarget").and_return("localhost").once()

        self.plugin_handler.LogPluginExecution("plugin_to_log")

        execution_registry = self.plugin_handler.ExecutionRegistry["localhost"]
        assert_that(execution_registry, has_item("plugin_to_log"))

    def test_GetLastPluginExecution_for_an_executed_plugin_should_return_the_index(self):
        self.core_mock.Config.should_receive("GetTarget").and_return("localhost")
        plugin = self._get_plugin_example()
        self.plugin_handler.LogPluginExecution(plugin)

        index = self.plugin_handler.GetLastPluginExecution(plugin)
        execution_registry = self.plugin_handler.ExecutionRegistry["localhost"]

        assert_that(execution_registry[index], equal_to(plugin))

    def test_HasPluginExecuted(self):
        self.core_mock.Config.should_receive("GetTarget").and_return("localhost")
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.HasPluginExecuted(plugin), is_(False))
        self.plugin_handler.LogPluginExecution(plugin)
        assert_that(self.plugin_handler.HasPluginExecuted(plugin), is_(True))

    def test_HasPluginCategoryRunSinceLastTime(self):
        self.core_mock.Config.should_receive("GetTarget").and_return("localhost")
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.HasPluginCategoryRunSinceLastTime(plugin, ["passive"]), is_(False))
        self.plugin_handler.LogPluginExecution(plugin)
        assert_that(self.plugin_handler.HasPluginCategoryRunSinceLastTime(plugin, ["passive"]), is_(True))

    def test_PluginAlreadyRun_should_check_the_filesystem_to_know_if_has_run(self):
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("exists").and_return(True)
        self.core_mock.Config.should_receive("Get").and_return("Plugin/output/dir")
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.PluginAlreadyRun(plugin))

    def test_GetLastPluginExecution_for_a_given_plugin_should_return_a_negative_value_if_not_executed(self):
        self.core_mock.Config.should_receive("GetTarget").and_return("localhost").once()
        plugin = self._get_plugin_example()

        value = self.plugin_handler.GetLastPluginExecution(plugin)

        assert_that(value, equal_to(-1))

    def test_ValidateAndFormatPluginList_returns_a_validated_list_of_plugins(self):
        plugin_list = ["HTTP_Methods_and_XST",
                       "AJAX_Vulnerabilities"]

        expected_values = ["OWASP-CM-008", "OWASP-AJ-001"]

        validated_list = self.plugin_handler.ValidateAndFormatPluginList(plugin_list)

        for value in expected_values:
            assert_that(validated_list, has_item(value))

    def test_ProcessPlugin_should_run_the_specified_plugin(self):
        self._prepare_for_ProcessPlugin_test()
        self.plugin_handler.should_receive("RunPlugin").once()
        status, plugin = self._create_args_for_ProcessPlugin()

        self.plugin_handler.ProcessPlugin(PLUGINS_DIR, plugin, status)

        assert_that(status["SomeSuccessful"])

    def test_ProcessPlugin_with_KeyBoardInterrupt_should_abort_plugin_execution(self):
        self._prepare_for_ProcessPlugin_test()
        self.plugin_handler.should_receive("RunPlugin").and_raise(KeyboardInterrupt)
        self.plugin_handler.should_receive("SavePluginInfo").once()
        self.core_mock.Error = flexmock()
        self.core_mock.Error.should_receive("UserAbort").once()
        status, plugin = self._create_args_for_ProcessPlugin()

        self.plugin_handler.ProcessPlugin(PLUGINS_DIR, plugin, status)

        assert_that(status["SomeAborted"])

    def test_IsChosenPlugin_should_be_true_because_the_web_plugins_are_enabled(self):
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.IsChosenPlugin(plugin))

    def test_IsActiveTestingPossible_should_be_false_with_the_current_fixture(self):
        assert_that(self.plugin_handler.IsActiveTestingPossible(), is_(False))

    def test_SavePluginInfo_should_save_to_DB_and_to_the_reporter(self):
        self.core_mock.DB, self.core_mock.Reporter = flexmock(), flexmock()
        self.core_mock.DB.DBHandler = flexmock()
        self.core_mock.DB.should_receive("SaveDBs").once()
        self.core_mock.Reporter.should_receive("SavePluginReport").once()

        self.plugin_handler.SavePluginInfo("PluginOutput", "Plugin")

    def test_NormalRequestsAllowed_with_the_current_options(self):
        # quiet profile specified in the environment
        assert_that(self.plugin_handler.NormalRequestsAllowed())

    def test_if_is_possible_to_make_requests(self):
        # more than grep plugins are enabled
        assert_that(self.plugin_handler.RequestsPossible())

    def test_CanPluginRun(self):
        self.core_mock.should_receive("IsTargetUnreachable").and_return(False)
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("PluginAlreadyRun").and_return(False)
        self.plugin_handler.should_receive("force_overwrite").and_return(False)
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.CanPluginRun(plugin))

    def test_CanPluginRun_when_the_plugin_has_already_run(self):
        self.core_mock.should_receive("IsTargetUnreachable").and_return(False)
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("PluginAlreadyRun").and_return(True)
        self.plugin_handler.should_receive("force_overwrite").and_return(False)
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.CanPluginRun(plugin, True), is_(False))

    def test_that_a_plugin_cannot_run_if_the_target_is_unreachable(self):
        self.core_mock.should_receive("IsTargetUnreachable").and_return(True)
        plugin = self._get_plugin_example()

        assert_that(self.plugin_handler.CanPluginRun(plugin, True), is_(False))

    def test_RunPlugin_has_to_look_for_the_plugin_in_the_filesystem_and_run_it(self):
        plugin = self._get_plugin_example()
        self.core_mock.DB = flexmock()
        self.core_mock.DB.Debug = flexmock()
        self.core_mock.DB.Debug.should_receive("Add").once()
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("GetModule.run").once()
        self.plugin_handler.should_receive("SavePluginInfo").once()

        self.plugin_handler.RunPlugin(PLUGINS_DIR, plugin)

    @unittest.skip("Infinite loop prevents this test to finish")
    def test_ProcessPluginsForTargetList_with_multiprocessing(self):
        num_cores = 1
        num_proc_per_core = 4
        flexmock(multiprocessing).should_receive("cpu_count").and_return(num_cores)
        self.core_mock.Config.should_receive("GetProcessPerCore").and_return(num_proc_per_core)
        num_process = num_cores * num_proc_per_core
        plugins_path = path.abspath("test_cases/resources/plugins_dir/web")
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("GetPluginGroupDir").and_return(plugins_path)
        self.plugin_handler.should_receive("get_plugins_in_order").and_return(["plugin1", "plugin2", "plugin3", "plugin4", "plugin5", "plugin6", "plugin7", "plugin8"])
        def fake_worker(work,queue,start,status):
            # I has to consume the items from the queue not to get a deadlock
            while True:
                try:
                    work = queue.get()
                    if work == (): sys.exit()
                except Queue.Empty:
                    pass
                finally:
                    time.sleep(0.5)
        self.plugin_handler.worker = fake_worker
        def fake_output(q): pass  #  In this test we are not taking care of the commands output
        self.plugin_handler.output = fake_output

        self.init_stdout_recording()
        self.plugin_handler.ProcessPluginsForTargetList("web", {}, ["target1", "target2", "target3", "target4"])
        stdout_content = self.get_recorded_stdout_and_close()

        assert_that(stdout_content, contains_string("number of workers " + str(num_process)))
        # Restore the num. of process as the config object is not renewed
        self.core_mock.Config.should_receive("GetProcessPerCore").and_return(1)

    def test_ProcessPluginsForTargetList_with_net_plugins(self):
        self.core_mock.Config.should_receive("Get").with_args("PORTWAVES").and_return("10")
        self.core_mock.Config.should_receive("Get").with_args("PLUGINS_DIR").and_return(PLUGINS_DIR)
        self.core_mock.Config.should_receive("GetTcpPorts").and_return(range(11)[1:])
        scanner = self.plugin_handler.scanner
        scanner.should_receive("scan_network").once()
        scanner.should_receive("probe_network").and_return([]).times(1)
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("SwitchToTarget").times(1)
        self.plugin_handler.should_receive("get_plugins_in_order_for_PluginGroup").and_return(["plugin1"])
        self.plugin_handler.should_receive("ProcessPlugin").times(1)

        self.plugin_handler.ProcessPluginsForTargetList("network", {}, ["target1"])

    def test_all_Show_methods_should_print_output_to_stdout(self):
        output = []
        self.init_stdout_recording()
        self.plugin_handler.ShowAuxPluginsBanner()
        output.append(self.get_recorded_stdout(True))
        self.plugin_handler.ShowWebPluginsBanner()
        output.append(self.get_recorded_stdout(True))
        self.plugin_handler.ShowPluginGroupPlugins("web")
        output.append(self.get_recorded_stdout(True))
        self.plugin_handler.ShowPluginGroupPlugins("auxiliary")
        output.append(self.get_recorded_stdout(True))
        self.plugin_handler.ShowPluginGroupPlugins("network")
        output.append(self.get_recorded_stdout_and_close())

        for element in output:
            assert_that(element is not None and element != "")

    def _get_options(self):
        return {"Simulation": False,
                "Scope": "localhost",
                "PluginGroup": "web",
                "PluginType": "quiet",
                "Algorithm": "breadth",
                "ListPlugins": None,
                "OnlyPlugins": None,
                "ExceptPlugins": None}

    def _prepare_for_ProcessPlugin_test(self):
        self.core_mock.Config.should_receive("GetTarget").and_return("localhost")
        self.core_mock.Timer = flexmock()
        self.core_mock.Timer.should_receive("StartTimer").once()
        self.core_mock.Timer.should_receive("GetStartDateTimeAsStr").once()
        flexmock(self.plugin_handler)
        self.plugin_handler.should_receive("CanPluginRun").and_return(True).once()

    def _get_plugin_example(self):
        return {'Args': '', 'Code': 'OWASP-IG-005', 'Group': 'web', 'Name': 'Application_Discovery', 'File': 'Application_Discovery@OWASP-IG-005.py', 'Title': 'Application Discovery', 'Descrip': '', 'Type': 'passive'}

    def _create_args_for_ProcessPlugin(self):
        status = {}
        plugin = {"Title": "plugin title",
                  "Type": "plugin type"}
        return status, plugin
