from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from hamcrest import *
from framework.plugin.plugin_params import PluginParams
import re
from hamcrest.library.text.stringmatches import matches_regexp


class PluginParamsTests(BaseTestCase):

    def before(self):
        self.core_mock = flexmock()
        self.plugin_params = PluginParams(self.core_mock, {'Args': ['arg1=val1', "arg2=val2"]})

    def test_ProcessArgs(self):
        assert_that(self.plugin_params.ProcessArgs(), is_(True))
        assert_that(self.plugin_params.Args["arg1"], is_("val1"))
        assert_that(self.plugin_params.Args["arg2"], is_("val2"))

    def test_ListArgs_should_print_the_args_to_the_stdout(self):
        args = {"arg_name": "arg_value"}

        self.init_stdout_recording()
        self.plugin_params.ListArgs(args)
        output = self.get_recorded_stdout_and_close()

        assert_that(output is not None)

    def test_ShowParamInfo_should_print_the_params_to_the_stdout(self):
        args = {"Description": "plugin description",
                "Mandatory": {"arg_name": "arg_value"},
                "Optional": {"arg_name": "arg_value"}}
        plugin = self._get_plugin_example()
        self.core_mock.Error = flexmock()
        self.core_mock.Error.should_receive("FrameworkAbort").once()

        self.init_stdout_recording()
        self.plugin_params.ShowParamInfo(args, plugin)
        output = self.get_recorded_stdout_and_close()

        assert_that(output is not None)

    def test_CheckArgList_should_be_ok(self):
        plugin = self._get_plugin_example()
        args = {"Mandatory": [], "Optional": [], "Description": ""}

        assert_that(self.plugin_params.CheckArgList(args, plugin))

    def test_CheckArgList_with_missing_Mandatory_and_Optional_args(self):
        self.core_mock.Error = flexmock()
        self.core_mock.Error.should_receive("Add").with_args(re.compile(".*Mandatory.*Optional")).once()
        plugin = self._get_plugin_example()

        self.plugin_params.CheckArgList({}, plugin)

    def test_CheckArgList_with_missing_description_arg(self):
        self.core_mock.Error = flexmock()
        self.core_mock.Error.should_receive("Add").with_args(re.compile(".*requires.*Description")).once()
        plugin = self._get_plugin_example()
        args = {"Mandatory": [], "Optional": []}

        self.plugin_params.CheckArgList(args, plugin)

    def test_SetArgsBasic_sets_the_args_to_the_plugin(self):
        plugin = self._get_plugin_example()
        args = {"arg1": "val1", "arg2": "val2"}
        self.plugin_params.Args = args

        assert_that(self.plugin_params.SetArgsBasic(args, plugin), equal_to([args]))
        assert_that(plugin["Args"], matches_regexp(".*arg1=val1.*"))
        assert_that(plugin["Args"], matches_regexp(".*arg2=val2.*"))

    def test_SetConfig_is_a_wrapper(self):
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("Set").with_args("_arg1", "val1").once()
        args = {"arg1": "val1"}

        self.plugin_params.SetConfig(args)

    def test_GetArgList_returns_the_args_we_ask_for(self):
        arg_list = ["arg1", "arg2"]
        plugin = self._get_plugin_example()

        result = self.plugin_params.GetArgList(arg_list, plugin)

        assert_that(result["arg1"], is_("val1"))
        assert_that(result["arg2"], is_("val2"))

    def test_GetArgList_registers_an_error_for_not_foud_args(self):
        self.core_mock.Error = flexmock()
        self.core_mock.Error.should_receive("Add").once()
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("IsSet").and_return(False)
        arg_list = ["non_existent_arg"]
        plugin = self._get_plugin_example()

        result = self.plugin_params.GetArgList(arg_list, plugin)

        assert_that(result, is_({}))
        assert_that(plugin["ArgError"], is_(True))

    def test_GetArgs(self):
        args = {"Mandatory": ["arg1"],
                "Optional": ["arg2"],
                "Description": "description"}
        plugin = self._get_plugin_example()
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("IsSet").and_return(False)

        result = self.plugin_params.GetArgs(args, plugin)

        assert_that(result[0]["arg1"], is_("val1"))
        assert_that(result[0]["arg2"], is_("val2"))

    def _get_plugin_example(self):
        return {'Args': '', 'Code': 'OWASP-IG-005', 'Group': 'web', 'Name': 'Application_Discovery', 'File': 'Application_Discovery@OWASP-IG-005.py', 'Title': 'Application Discovery', 'Descrip': '', 'Type': 'passive'}