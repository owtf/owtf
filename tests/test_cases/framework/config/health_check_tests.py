from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from framework.config.health_check import HealthCheck


class HealthCheckTests(BaseTestCase):

    def before(self):
        self.config = flexmock()
        self.core_mock = flexmock()

    def test_Run_with_all_installed_tools_should_be_successful(self):
        self._prepare_core_mock_for_health_check_Run()
        health_check = HealthCheck(self.core_mock)
        flexmock(health_check)
        health_check.should_receive("is_installed").and_return(True)
        health_check.should_receive("print_success").once()

        health_check.run()

    def test_Run_with_missing_tools_should_warn_the_user(self):
        self._prepare_core_mock_for_health_check_Run()
        health_check = HealthCheck(self.core_mock)
        flexmock(health_check)
        health_check.should_receive("is_installed").and_return(False)
        health_check.should_receive("print_warning").once()

        health_check.run()

    def _prepare_core_mock_for_health_check_Run(self):
        config_dict = {'string': self._get_config_dictionary()}
        self.config.should_receive("GetConfig").and_return(config_dict).once()
        self.config.should_receive("StripKey").and_return("TOOL_X")
        self.core_mock.Config = self.config

    def _get_config_dictionary(self):
        return {"TOOL_ONE": "path1", "TOOL_TWO": "path2"}
