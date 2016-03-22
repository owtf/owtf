from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.shell.blocking_shell import Shell
from tests.testing_framework.shell.environments import InteractiveShellEnvironmentBuilder
from hamcrest.library.text.stringmatches import matches_regexp
import logging
from framework.lib.general import get_default_logger
import sys
from tests.testing_framework.doubles.mock import StreamMock


class BlockingShellTests(BaseTestCase):

    def before(self):
        environment_builder = InteractiveShellEnvironmentBuilder()
        environment_builder._create_core_mock()
        self.core_mock = environment_builder.core_mock
        self.shell = Shell(self.core_mock)

    def test_shell_exec_monitor_runs_a_command_logging_the_output(self):
        stream = StreamMock()
        self.redirect_logging_to_stream(stream)
        command = 'pwd'
        expected_command_output = self.get_abs_path(".")
        expected_time_logging_message = "Execution Start Date/Time"

        command_output = self.shell.shell_exec_monitor(command)

        assert_that(command_output, matches_regexp(expected_command_output))
        assert_that(stream.get_content(), matches_regexp(expected_time_logging_message))
        assert_that(stream.get_content(), matches_regexp(expected_command_output))

    def test_shell_exec_monitor_with_KeyboardInterrupt_should_cancel_the_command(self):
        subprocess = flexmock()
        subprocess.stdout = flexmock()
        subprocess.stdout.should_receive("readline").and_raise(KeyboardInterrupt).once()
        flexmock(self.shell)
        self.shell.should_receive("create_subprocess").and_return(subprocess)

        def fake_finish_command(arg1, cancelled):
            assert_that(cancelled, is_(True))
        self.shell.FinishCommand = fake_finish_command

        self.shell.shell_exec_monitor("pwd")

    def redirect_logging_to_stream(self, stream):
        logging_handler = logging.StreamHandler(stream)
        logger = get_default_logger("info")
        logger.addHandler(logging_handler)
