from tests.testing_framework.base_test_cases import BaseTestCase
from tests.testing_framework.utils import ExpensiveResourceProxy
from flexmock import flexmock
from hamcrest import *
from tests.testing_framework.config.environments import ConfigEnvironmentBuilder
from framework.lib.exceptions import PluginAbortException
from tests.testing_framework.config.config_state import ConfigState


class ConfigTests(BaseTestCase):

    config_proxy = ExpensiveResourceProxy(ConfigEnvironmentBuilder())

    def before(self):
        self.config = self.__class__.config_proxy.get_instance()
        self.config_status_backup = ConfigState(self.config)
        self.config.Core.DevMode = False

    def after(self):
        ConfigState.restore_state(self.config, self.config_status_backup)

    def test_ProcessOptions_has_to_run_a_health_check_and_set_some_values(self):
        health_check = flexmock()
        health_check.should_receive("run").once()
        self.config.HealthCheck = health_check
        flexmock(self.config)
        self.config.should_receive("LoadProfilesAndSettings").once()
        self.config.should_receive("LoadPluginTestGroups").once()

        self.config.ProcessOptions(self._get_options())

        assert_that(config_property_is_defined("FORCE_OVERWRITE"))
        assert_that(config_property_is_defined("INTERACTIVE"))
        assert_that(config_property_is_defined("SIMULATION"))
        assert_that(config_property_is_defined("PORTWAVES"))

    def test_that_Set_records_the_parameter_in_the_internal_dictionary(self):
        self.config.Set("key", "value")

        assert_that(config_property_is_defined("key"))

    def test_DeriveFromTarget_with_web_or_net_group_should_set_some_config_properties(self):
        options = self._get_options()
        options["Scope"] = ["http://localhost"]
        flexmock(self.config)
        self.config.should_receive("GetIPFromHostname").and_return("127.0.0.1")
        self.config.should_receive("DeriveConfigFromURL").once()
        method_backup = self.config.Get

        def fake_get(key):
            if key == "host_ip": return "127.0.0.1"
            elif key == "port_number": return "80"
            elif key == "OUTPUT_PATH": return "some/path"
        self.config.Get = fake_get

        self.config.DeriveFromTarget(options)
        self.config.Get = method_backup  # Restore original method

        assert_that(config_property_is_defined("REVIEW_OFFSET"))
        assert_that(config_property_is_defined("SUMMARY_HOST_IP"))
        assert_that(config_property_is_defined("SUMMARY_PORT_NUMBER"))
        assert_that(config_property_is_defined("REPORT_TYPE"))

    def test_DeriveFromTarget_with_aux_group_should_set_some_config_properties(self):
        options = self._get_options()
        options["Scope"] = ["http://localhost:8080"]
        options["PluginGroup"] = "auxiliary"
        self.config.Set("OUTPUT_PATH", "some/path")

        self.config.DeriveFromTarget(options)

        assert_that(config_property_is_defined("AUX_OUTPUT_PATH"))
        assert_that(config_property_is_defined("HTML_DETAILED_REPORT_PATH"))
        assert_that(config_property_is_defined("REVIEW_OFFSET"))
        assert_that(config_property_is_defined("SUMMARY_HOST_IP"))
        assert_that(config_property_is_defined("SUMMARY_PORT_NUMBER"))
        assert_that(config_property_is_defined("REPORT_TYPE"))
        assert_that(target_is("auxiliary"))

    def test_DeriveGlobalSettings_should_set_some_global_config_settings(self):
        self.config.Set("OUTPUT_PATH", "some/path")
        self.config.Set("USER_AGENT", "User Agent")
        self.config.Set("HTML_REPORT", "")

        self.config.DeriveGlobalSettings()

        assert_that(config_property_is_defined("FRAMEWORK_DIR"))
        assert_that(config_property_is_defined("UNREACHABLE_DB"))
        assert_that(config_property_is_defined("RUN_DB"))
        assert_that(config_property_is_defined("ERROR_DB"))
        assert_that(config_property_is_defined("SEED_DB"))
        assert_that(config_property_is_defined("SUMMARY_HTMLID_DB"))
        assert_that(config_property_is_defined("DEBUG_DB"))
        assert_that(config_property_is_defined("PLUGIN_REPORT_REGISTER"))
        assert_that(config_property_is_defined("DETAILED_REPORT_REGISTER"))
        assert_that(config_property_is_defined("COMMAND_REGISTER"))
        assert_that(config_property_is_defined("USER_AGENT_#"))
        assert_that(config_property_is_defined("SHORT_USER_AGENT"))
        assert_that(config_property_is_defined("HTML_REPORT_PATH"))

    def test_DeriveURLSettings_sets_url_settings(self):
        options = {"PluginGroup": "network",
                   "RPort": "80",
                   "OnlyPlugins": None}
        target = "http://localhost"

        self.config.DeriveURLSettings(target, options)

        assert_that(config_property_is_defined("target_url"))
        assert_that(config_property_is_defined("host_path"))
        assert_that(config_property_is_defined("url_scheme"))
        assert_that(config_property_is_defined("port_number"))
        assert_that(config_property_is_defined("host_name"))
        assert_that(config_property_is_defined("host_ip"))
        assert_that(config_property_is_defined("ip_url"))
        assert_that(config_property_is_defined("top_domain"))

    def test_DeriveOutputSettingsFromURL_sets_output_settings(self):
        self.config.Set("host_ip", "127.0.0.1")
        self.config.Set("port_number", "80")

        self.config.DeriveOutputSettingsFromURL("http://localhost")

        assert_that(config_property_is_defined("host_output"))
        assert_that(config_property_is_defined("port_output"))
        assert_that(config_property_is_defined("url_output"))
        assert_that(config_property_is_defined("partial_url_output_path"))
        assert_that(config_property_is_defined("PARTIAL_REPORT_REGISTER"))
        assert_that(config_property_is_defined("HTML_DETAILED_REPORT_PATH"))
        assert_that(config_property_is_defined("URL_REPORT_LINK_PATH"))

    def test_InitHTTPDBs_sets_the_DB_locations_in_the_internal_dictionary(self):
        self.config.InitHTTPDBs("path/to/db")

        assert_that(transaction_DBs_path_are_defined())
        assert_that(potential_DBs_path_are_defined())
        assert_that(other_DBs_path_are_defined())

    def test_GetFileName_should_obtain_name_from_the_path(self):
        path = "/some/path/"
        expected_filename = "file.py"
        self.config.Set("TEST_FILENAME", path + expected_filename)

        obtained_filename = self.config.GetFileName("TEST_FILENAME", True)

        assert_that(obtained_filename, equal_to(expected_filename))

    def test_LoadResourcesFromFile_parses_resources_succesfully(self):
        path_to_file = self.get_abs_path("test_cases/resources/resources_example.cfg")

        self.config.LoadResourcesFromFile(path_to_file)

        resources = self.config.Resources
        assert_that(resources, has_key("RESOURCETYPE"))
        assert_that(resources["RESOURCETYPE"][0], equal_to(["ResourceName", "Resource"]))

    def test_LoadProfiles_should_get_default_resource_files_and_parse_them(self):
        self.config.LoadProfiles([])

        profiles = self.config.Profiles

        assert_that(profiles, has_key("web"))
        assert_that(profiles, has_key("network"))
        assert_that(profiles, has_key("r"))  # r for Resources
        assert_that(profiles, has_key("g"))  # g for General

    def test_GetResources_should_return_the_resources_associated_to_a_type(self):
        self.config.LoadProfiles([])

        web_resources = self.config.GetResources("web")

        assert_that(web_resources is not None)

    def test_GetResources_should_return_an_empty_list_and_a_warning_for_unkwnown_types(self):
        self.config.LoadProfiles([])

        self.init_stdout_recording()
        resources = self.config.GetResources("unkwnown_type")
        output = self.get_recorded_stdout_and_close()

        assert_that(resources, equal_to([]))
        assert_that(output, contains_string("is not defined"))

    def test_that_TCP_and_UDP_port_listing_could_be_generated_with_config_object(self):
        assert_that(self.config.GetTcpPorts(10, 100) is not None)
        assert_that(self.config.GetUdpPorts(10, 100) is not None)

    def _get_options(self):
        return {"Force_Overwrite": False,
                "Interactive": False,
                "Simulation": True,
                "PluginGroup": "web",
                "PortWaves": [10,100],
                'Scope': [],
                "Profiles": {}}


def config_property_is_defined(key):
    config = ConfigTests.config_proxy.get_instance()
    try:
        value = config.Get(key)
        return value is not None
    except PluginAbortException:
        return False


def target_is(target):
    config = ConfigTests.config_proxy.get_instance()
    return target == config.GetTarget()


def transaction_DBs_path_are_defined():
    try:
        assert_that(config_property_is_defined("TRANSACTION_LOG_TXT"))
        assert_that(config_property_is_defined("TRANSACTION_LOG_HTML"))
        assert_that(config_property_is_defined("TRANSACTION_LOG_TRANSACTIONS"))
        assert_that(config_property_is_defined("TRANSACTION_LOG_REQUESTS"))
        assert_that(config_property_is_defined("TRANSACTION_LOG_RESPONSE_HEADERS"))
        assert_that(config_property_is_defined("TRANSACTION_LOG_RESPONSE_BODIES"))
        assert_that(config_property_is_defined("TRANSACTION_LOG_FILES"))
        return True
    except AssertionError:
        return False


def potential_DBs_path_are_defined():
    try:
        assert_that(config_property_is_defined("POTENTIAL_ALL_URLS_DB"))
        assert_that(config_property_is_defined("POTENTIAL_ERROR_URLS_DB"))
        assert_that(config_property_is_defined("POTENTIAL_FILE_URLS_DB"))
        assert_that(config_property_is_defined("POTENTIAL_IMAGE_URLS_DB"))
        assert_that(config_property_is_defined("POTENTIAL_FUZZABLE_URLS_DB"))
        assert_that(config_property_is_defined("POTENTIAL_EXTERNAL_URLS_DB"))
        return True
    except AssertionError:
        return False


def other_DBs_path_are_defined():
    try:
        assert_that(config_property_is_defined("HTMLID_DB"))
        assert_that(config_property_is_defined("ALL_URLS_DB"))
        assert_that(config_property_is_defined("ERROR_URLS_DB"))
        assert_that(config_property_is_defined("FILE_URLS_DB"))
        assert_that(config_property_is_defined("IMAGE_URLS_DB"))
        assert_that(config_property_is_defined("FUZZABLE_URLS_DB"))
        assert_that(config_property_is_defined("EXTERNAL_URLS_DB"))
        return True
    except AssertionError:
        return False
