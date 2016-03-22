from tests.testing_framework.base_test_cases import BaseTestCase
from tests.testing_framework.utils import ExpensiveResourceProxy
from hamcrest import *
from os import path
from tests.testing_framework.config.environments import PluginConfigEnvironmentBuilder

PLUGIN_ORDER_EXAMPLE_FILE = path.abspath("test_cases/resources/web_plugin_order_example.cfg")


class PluginConfigTests(BaseTestCase):
    """
    WARNING: SLOW TESTS, as all the plugin configuration is loaded from
             the config files, and the filesystem is scanned in order
             to find the plugins.
    """
    plugin_config_proxy = ExpensiveResourceProxy(PluginConfigEnvironmentBuilder())

    def before(self):
        self.plugin_config = self.__class__.plugin_config_proxy.get_instance()

    def test_GetAllTypes_should_return_a_list_with_all_types(self):
        all_types = self.plugin_config.GetAllTypes()

        assert_that(all_types, has_item('active'))
        assert_that(all_types, has_item('bruteforce'))
        assert_that(all_types, has_item('dos'))
        assert_that(all_types, has_item('exploit'))
        assert_that(all_types, has_item('external'))
        assert_that(all_types, has_item('grep'))
        assert_that(all_types, has_item('passive'))
        assert_that(all_types, has_item('rce'))
        assert_that(all_types, has_item('se'))
        assert_that(all_types, has_item('selenium'))
        assert_that(all_types, has_item('semi_passive'))
        assert_that(all_types, has_item('smb'))

    def test_GetAllGroups_should_return_a_list_with_all_groups(self):
        all_groups = self.plugin_config.GetAllGroups()

        assert_that(all_groups, has_item('auxiliary'))
        assert_that(all_groups, has_item('network'))
        assert_that(all_groups, has_item('web'))

    def test_GetTypesForGroup_aux_should_return_a_list_with_its_types(self):
        aux_types = self.plugin_config.GetTypesForGroup("auxiliary")

        assert_that(aux_types, has_length(7))

    def test_GetTypesForGroup_net_should_return_a_list_with_its_types(self):
        net_types = self.plugin_config.GetTypesForGroup("network")

        assert_that(net_types, has_length(2))

    def test_GetTypesForGroup_web_should_return_a_list_with_its_types(self):
        web_types = self.plugin_config.GetTypesForGroup("web")

        assert_that(web_types, has_length(5))

    def test_GetTypesForGroup_with_non_existing_group_should_return_empty_list_and_warning(self):
        self.init_stdout_recording()
        types = self.plugin_config.GetTypesForGroup("non_existing_group")
        warning = self.get_recorded_stdout_and_close()

        assert_that(types, has_length(0))
        assert_that(warning, contains_string("not found"))

    def test_GetGroupsForPlugins_should_return_a_group_given_a_plugin(self):
        groups = self.plugin_config.GetGroupsForPlugins(["Application_Discovery"])

        assert_that(groups, has_item("web"))

    def test_GetPlugin_should_return_the_first_plugin_matching_the_criteria(self):
        criteria = {"Group": "web",
                    "Type": "active"}
        plugin = self.plugin_config.GetPlugin(criteria)

        assert_that(plugin is not None)

    def test_GetPlugin_with_no_matching_criteria_should_return_None_and_print_warning(self):
        self.init_stdout_recording()
        plugin = self.plugin_config.GetPlugin({"Group": "non_existing_group"}, ShowWarnings=True)
        warning = self.get_recorded_stdout_and_close()

        assert_that(plugin is None)
        assert_that(warning, contains_string("WARNING"))

    def test_GetAll_should_return_plugins_that_math_the_given_group_and_type(self):
        plugin_group = "network"
        plugin_type = "bruteforce"
        plugins = self.plugin_config.GetAll(plugin_group, plugin_type)

        assert_that(plugins, has_length(greater_than(0)))
        for plugin in plugins:
            assert_that(plugin['Group'], is_(plugin_group))
            assert_that(plugin['Type'], is_(plugin_type))

    def test_DeriveAllowedTypes_for_web_should_enable_all_plugins_by_default(self):
        self.plugin_config.DeriveAllowedTypes("web", [])

        assert_that(self.plugin_config.AllowedPluginTypes["web"], has_length(5))

    def test_DeriveAllowedTypes_for_web_should_enable_all_plugins(self):
        expected_types = ['active', 'external', 'grep', 'passive', 'semi_passive']
        self.plugin_config.DeriveAllowedTypes("web", ["all"])

        print self.plugin_config.AllowedPluginTypes["web"]

        for plugin_type in expected_types:
            assert_that(self.plugin_config.AllowedPluginTypes["web"], has_item(plugin_type))


    def test_DeriveAllowedTypes_for_web_with_quiet_TypeFilter_should_include_passive_and_semi_passive(self):
        self.plugin_config.DeriveAllowedTypes("web", ["quiet"])

        assert_that(self.plugin_config.AllowedPluginTypes["web"], has_item("passive"))
        assert_that(self.plugin_config.AllowedPluginTypes["web"], has_item("semi_passive"))

    def test_DeriveAllowedTypes_for_web_with_semi_passive_or_active_should_include_grep_plugins(self):
        self.plugin_config.DeriveAllowedTypes("web", ["semi_passive"])
        assert_that(self.plugin_config.AllowedPluginTypes["web"], has_item("grep"))

        self.plugin_config.DeriveAllowedTypes("web", ["active"])
        assert_that(self.plugin_config.AllowedPluginTypes["web"], has_item("grep"))

    def test_DeriveAllowedTypes_for_net_should_include_all_types(self):
        self.plugin_config.DeriveAllowedTypes("network", ["all"])

        assert_that(self.plugin_config.AllowedPluginTypes["network"], has_item("active"))
        assert_that(self.plugin_config.AllowedPluginTypes["network"], has_item("bruteforce"))

    def test_DeriveAllowedTypes_for_net_with_specific_filter_should_only_include_selected(self):
        self.plugin_config.DeriveAllowedTypes("network", ["active"])

        assert_that(self.plugin_config.AllowedPluginTypes["network"], has_length(1))
        assert_that(self.plugin_config.AllowedPluginTypes["network"], has_item("active"))

    def test_LoadPluginOrderFromFile_processing(self):
        self.plugin_config.LoadPluginOrderFromFile("web", PLUGIN_ORDER_EXAMPLE_FILE)
        web_order = self.plugin_config.PluginOrder["web"]
        web_plugin_names = ["Application_Discovery",   # Order defined in the resource file
                            "AJAX_Vulnerabilities",
                            "Application_Discovery",
                            "HTTP_Methods_and_XST",
                            "Application_Configuration_Management"]

        for i, plugin in enumerate(web_order):
            assert_that(plugin["Name"], equal_to_ignoring_case(web_plugin_names[i]))
