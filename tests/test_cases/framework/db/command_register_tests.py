from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.db.command_register import CommandRegister


class CommandRegisterTests(BaseTestCase):

    def before(self):
        self.core_mock = flexmock()

    def test_Add_should_save_a_command_through_a_core_call(self):
        self._mock_db_method_once("Add")
        command_register = self._create_command_register_with_core_mock()

        command_register.Add(self._create_command_dictionary())

    def test_Search_should_use_a_core_call(self):
        self._mock_db_method_once("Search")
        command_register = self._create_command_register_with_core_mock()

        command_register.Search("Criteria")

    def test_AlreadyRegistered_should_return_False_for_not_registered_commands(self):
        command_register = self._create_command_register_with_core_mock()
        flexmock(command_register)
        command_register.should_receive("Search").and_return([]).once()

        registered = command_register.AlreadyRegistered("Command")

        assert_that(registered, is_(False))

    def test_AlreadyRegistered_should_return_non_False_for_registered_commands(self):
        command_register = self._create_command_register_with_core_mock()
        flexmock(command_register)
        command_register.should_receive("Search").and_return([{'Status': 'Finished',
                                                               'Target': 'target'}]).once()
        registered = command_register.AlreadyRegistered("Command")

        assert_that(registered, is_not(False))
        assert_that(registered is not None)

    def _mock_db_method_once(self, method):
        db_mock = flexmock()
        db_mock.should_receive(method).once()
        self.core_mock.DB = db_mock

    def _create_command_register_with_core_mock(self):
        return CommandRegister(self.core_mock)

    def _create_command_dictionary(self):
        return {'Start': '',
                'End': '',
                'RunTime': '',
                'Status': '',
                'Target': '',
                'ModifiedCommand': '',
                'OriginalCommand': ''}
