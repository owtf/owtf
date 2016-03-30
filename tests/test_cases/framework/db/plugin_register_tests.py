from tests.testing_framework.base_test_cases import BaseTestCase
from flexmock import flexmock
from hamcrest import *
from framework.db.plugin_register import PluginRegister


class PluginRegisterTests(BaseTestCase):

    def before(self):
        self.core_mock = flexmock()
        self._mock_timer()
        self._mock_config()
        self.core_mock.DB = flexmock()
        self.core_mock.DB.DBHandler = flexmock()
        self.plugin_register = PluginRegister(self.core_mock)

    def test_NumPluginsForTarget_and_AlreadyRegistered_delegate_on_the_DB_Search_engine(self):
        self.core_mock.DB.should_receive("Search").and_return(["one result"]).times(2)
        plugin = self._get_plugin_example()

        self.plugin_register.AlreadyRegistered(plugin, "Path", "Target")
        self.plugin_register.NumPluginsForTarget("Target")

    def test_Add_uses_the_DB_to_register_a_plugin(self):
        self.core_mock.DB.should_receive("Add").once()
        flexmock(self.plugin_register)
        self.plugin_register.should_receive("AlreadyRegistered").and_return(False)
        plugin = self._get_plugin_example()

        self.plugin_register.Add(plugin, "Path", "Target")

    def _mock_timer(self):
        self.core_mock.Timer = flexmock()
        self.core_mock.Timer.should_receive("GetElapsedTimeAsStr").and_return("")
        self.core_mock.Timer.should_receive("GetEndDateTimeAsStr").and_return("")

    def _mock_config(self):
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("Get").and_return("")

    def _get_plugin_example(self):
        return {'Args': '',
                'Code': 'OWASP-IG-005',
                'Group': 'web',
                'Name': 'Application_Discovery',
                'File': 'Application_Discovery@OWASP-IG-005.py',
                'Title': 'Application Discovery',
                'Descrip': '',
                'Type': 'passive',
                'Start': '',
                'End': '',
                'RunTime': '',
                'Status': '',
                'Target': '',
                'ModifiedCommand': '',
                'OriginalCommand': ''}
