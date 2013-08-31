from tests.testing_framework.base_test_cases import BaseTestCase
from hamcrest import *
from flexmock import flexmock
from framework.db.run_manager import RunManager


class RunManagerTests(BaseTestCase):

    def before(self):
        self.core_mock = flexmock()

    def test_StartRun_should_start_a_timer_and_save_the_execution_to_DB(self):
        self._prepare_core_mock_for_StartRun()
        run_manager = self._create_RunManager_instance_with_core_mock()

        run_manager.StartRun("Command")

    def test_EndRun_should_get_timer_data_and_modify_a_record_in_DB(self):
        self._prepare_core_mock_for_EndRun()
        run_manager = self._create_RunManager_instance_with_core_mock()

        run_manager.EndRun()

    def _prepare_core_mock_for_StartRun(self):
        timer = self._mock_timer_for_StartRun()
        db = self._mock_DB_logging()
        self.core_mock.Timer = timer
        self.core_mock.DB = db

    def _mock_timer_for_StartRun(self):
        timer = flexmock()
        timer.should_receive("StartTimer").and_return(["Start", "Time"]).once()
        return timer

    def _mock_DB_logging(self):
        db = flexmock()
        db.should_receive("Add").once()
        return db

    def _create_RunManager_instance_with_core_mock(self):
        return RunManager(self.core_mock)

    def _prepare_core_mock_for_EndRun(self):
        timer = self._mock_timer_for_EndRun()
        db = self._mock_DB_for_EndRun()
        self.core_mock.Timer = timer
        self.core_mock.DB = db

    def _mock_timer_for_EndRun(self):
        timer = flexmock()
        timer.should_receive("GetCurrentDateTime").once()
        timer.should_receive("GetElapsedTimeAsStr").once()
        return timer

    def _mock_DB_for_EndRun(self):
        db = flexmock()
        db.should_receive("GetRecord").and_return({}).once()
        db.should_receive("ModifyRecord").once()
        return db
