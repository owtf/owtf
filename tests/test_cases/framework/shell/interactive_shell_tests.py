from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from tests.testing_framework.shell.environments import InteractiveShellEnvironmentBuilder
from framework.shell.async_subprocess import AsyncPopen
from hamcrest.library.text.stringmatches import matches_regexp
from tests.testing_framework.utils import ExpensiveResourceProxy


class InteractiveShellTests(BaseTestCase):

    shell_proxy = ExpensiveResourceProxy(InteractiveShellEnvironmentBuilder())

    def before(self):
        self.interactive_shell = self.__class__.shell_proxy.get_instance()

    def test_Open_has_to_create_a_new_shell_connection(self):
        assert_that(self.interactive_shell.Connection is not None)
        assert_that(isinstance(self.interactive_shell.Connection, AsyncPopen))

    def test_Run_command_in_a_shell(self):
        output = self.interactive_shell.Run('pwd')

        expected = self.get_abs_path(".")
        assert_that(output, matches_regexp(expected))

    def test_RunCommandList_runs_more_than_one_command_in_a_shell(self):
        output = self.interactive_shell.RunCommandList(['pwd', "echo 1234"])

        pwd_expected = self.get_abs_path(".")
        echo_expected = "1234"

        assert_that(output, matches_regexp(pwd_expected))
        assert_that(output, matches_regexp(echo_expected))

    def test_Close_should_kill_the_connection(self):
        #  As we are using the same instance for all the tests, it's necessary to make a backup
        #  of some methods and attributes, to make this test independent from the others.
        shell_backup = self._get_backup(self.interactive_shell, "Run", "Connection") 
        #{"Run": self.interactive_shell.Run,"Connection": self.interactive_shell.Connection}
        self.interactive_shell.Run = MethodMock(1, "exit")
        self.interactive_shell.Connection = flexmock()
        self.interactive_shell.Connection.should_receive("kill").once()

        try:
            self.interactive_shell.Close(None)
            assert_that(self.interactive_shell.Connection is None)
        finally:
            # Tear down
            self._restore_backup(self.interactive_shell, shell_backup)

    def _get_backup(self, target, *attrs):
        backup = {}
        for attr in attrs:
            backup[attr] = getattr(target, attr)
        return backup

    def _restore_backup(self, target, backup):
        for name, obj in backup.items():
            setattr(target, name, obj)


class MethodMock():

    def __init__(self, times, *args):
        self.times = times
        self.time_counter = 0
        self.args = args

    def __call__(self, *args):
        if self.times - self.time_counter > 0:
            for i, arg in enumerate(self.args):
                assert_that(args[i], equal_to(arg))
            self.time_counter += 1
        else:
            raise AssertionError("Method called " + self.time_counter + " times but expected " + self.times + " times.")
