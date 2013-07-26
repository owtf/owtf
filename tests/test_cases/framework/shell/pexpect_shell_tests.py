from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.shell.pexpect_shell import PExpectShell
from tests.testing_framework.shell.environments import InteractiveShellEnvironmentBuilder
from os import path
from hamcrest.library.text.stringmatches import matches_regexp


class PExpectShellTests(BaseTestCase):

    def before(self):
        environment_builder = InteractiveShellEnvironmentBuilder()
        environment_builder._create_core_mock()
        self.core_mock = environment_builder.core_mock
        self.pexpect_shell = PExpectShell(self.core_mock)

    def after(self):
        self.pexpect_shell.Close(None)

    def test_that_we_can_interact_with_external_programs_with_pexpect_shell(self):
        self.pexpect_shell.Open(self._get_options_example(), None)
        script = "python " + path.abspath("test_cases/resources/pexpect_script.py")

        self.pexpect_shell.Run(script)
        self.pexpect_shell.Expect("User: ")
        assert_that(self.pexpect_shell.Read(), equal_to("User: "))

        self.pexpect_shell.Run("user")
        assert_that(self.pexpect_shell.Expect("Test passed"))

    def _get_options_example(self):
        return {"ConnectVia": [['', "bash"]],
                "InitialCommands": None,
                "CommandsBeforeExit": None,
                "ExitMethod": "kill",
                "CommandsBeforeExitDelim": ";"}
