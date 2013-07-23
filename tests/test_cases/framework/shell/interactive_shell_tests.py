from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.shell.interactive_shell import InteractiveShell
from tests.testing_framework.shell.environments import InteractiveShellEnvironmentBuilder
from framework.shell.async_subprocess import AsyncPopen
from hamcrest.library.text.stringmatches import matches_regexp
from os import path
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

        expected = path.abspath(".")
        assert_that(output, matches_regexp(expected))
