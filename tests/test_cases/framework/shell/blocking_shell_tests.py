from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.shell.blocking_shell import Shell
from tests.testing_framework.shell.environments import InteractiveShellEnvironmentBuilder
from hamcrest.library.text.stringmatches import matches_regexp


class BlockingShellTests(BaseTestCase):

    def before(self):
        environment_builder = InteractiveShellEnvironmentBuilder()
        environment_builder._create_core_mock()
        self.core_mock = environment_builder.core_mock
        self.shell = Shell(self.core_mock)

    def test_shell_exec_monitor_runs_a_command_logging_the_output(self):
        command = 'pwd'
        expected_command_output = self.get_abs_path(".")
        expected_time_logging_message = "Execution Start Date/Time"

        self.init_stdout_recording()
        command_output = self.shell.shell_exec_monitor(command)
        stdout_content = self.get_recorded_stdout_and_close()

        assert_that(command_output, matches_regexp(expected_command_output))
        assert_that(stdout_content, matches_regexp(expected_command_output))

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