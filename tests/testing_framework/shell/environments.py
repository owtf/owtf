from flexmock import flexmock
from os import path
from framework.shell.interactive_shell import InteractiveShell
from framework.timer import Timer


class InteractiveShellEnvironmentBuilder():

    def __call__(self):
        self._create_core_mock()
        instance = InteractiveShell(self.core_mock)
        instance.Open(self._get_options_example(), None)
        return instance

    def _create_core_mock(self):
        self.core_mock = flexmock()
        self._mock_timer()
        self._mock_config()
        self._mock_error_handler()
        self._mock_db()

    def _mock_timer(self):
        self.core_mock.Timer = Timer()

    def _mock_config(self):
        self.core_mock.Config = flexmock()
        self.core_mock.Config.should_receive("Get").with_args("TARGET").and_return("localhost")
        self.core_mock.Config.Get = lambda arg:"localhost" if arg == "TARGET" else ""

    def _mock_error_handler(self):
        self.core_mock.Error = flexmock()
        self.core_mock.Error.should_receive("UserAbort").and_return("")

    def _mock_db(self):
        self.core_mock.DB = flexmock()
        self.core_mock.DB.CommandRegister = flexmock()
        self.core_mock.DB.CommandRegister.should_receive("AlreadyRegistered").and_return(False)
        self.core_mock.DB.CommandRegister.Add = lambda arg: True # Due to some flexmock bug with nested objects

    def _get_options_example(self):
        return {"ConnectVia": [['', 'bash']],
                "InitialCommands": None,
                "CommandsBeforeExit": None,
                "ExitMethod": "kill",
                "CommandsBeforeExitDelim": ";"}
