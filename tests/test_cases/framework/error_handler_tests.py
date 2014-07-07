from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.error_handler import ErrorHandler
from framework.lib.exceptions import FrameworkAbortException, \
                                     PluginAbortException
from framework import error_handler
import unittest


class ErrorHandlerTests(BaseTestCase):
    def before(self):
        self.core_mock = flexmock()

    def test_FrameworkAbort_printing_and_core_delegation(self):
        message = "Message"
        self.core_mock.should_receive('Finish').with_args(str, bool).once()
        error_handler = self._create_error_handler_with_core_mock()

        self.init_stdout_recording()
        error_handler.FrameworkAbort(message)
        stdout_content = self.get_recorded_stdout_and_close()

        assert_that(stdout_content is not None)

    @unittest.skip("Option 'e' (Exit) currently disabled")
    def test_UserAbort_with_options_Exit_and_Command_should_raise_an_exception(self):
        error_handler = self._create_error_handler_with_core_mock()
        flexmock(error_handler)
        error_handler.should_receive("get_option_from_user").and_return("e").once()

        try:
            error_handler.UserAbort("Command")
            self.fail("Exception expected")
        except FrameworkAbortException:
            pass  # Test passed

    def test_UserAbort_with_plugin_should_raise_and_exception(self):
        error_handler = self._create_error_handler_with_core_mock()
        flexmock(error_handler)

        try:
            error_handler.UserAbort("Plugin")
        except PluginAbortException:
            pass  # Test passed

    def test_LogError_saves_error_message_to_the_DB(self):
        message = "Error message"
        db_mock = flexmock()
        db_mock.should_receive("AddError").with_args(message).once()
        self.core_mock.DB = db_mock
        error_handler = self._create_error_handler_with_core_mock()

        error_handler.LogError(message)

    def test_LogError_shows_error_message_when_DB_is_unavailable(self):
        db_mock = flexmock()
        db_mock.should_receive("AddError").and_raise(AttributeError).once()
        self.core_mock.DB = db_mock
        error_handler = self._create_error_handler_with_core_mock()

        self.init_stdout_recording()
        error_handler.LogError("Error message")
        stdout_content = self.get_recorded_stdout_and_close()

        assert_that(stdout_content is not None)

    def test_Add_should_print_and_save_to_the_DB_a_non_OWTF_error(self):
        error_handler = self._create_error_handler_with_core_mock()
        flexmock(error_handler)
        error_handler.should_receive("LogError").once()

        self.init_stdout_recording()
        error_handler.Add("Error message", BugType="external")
        stdout_content = self.get_recorded_stdout_and_close()

        assert_that(stdout_content is not None)

    def test_Add_should_notify_the_user_when_an_OWTF_bug_is_found(self):
        error_handler = self._create_error_handler_with_core_mock()
        flexmock(error_handler)
        error_handler.should_receive("LogError").once()

        self.init_stdout_recording()
        error_handler.Add("Error message", BugType="owtf")
        stdout_content = self.get_recorded_stdout_and_close()

        assert_that(stdout_content is not None)

    def _create_error_handler_with_core_mock(self):
        return ErrorHandler(self.core_mock)
